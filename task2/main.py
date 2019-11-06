"""
Usage: main.py [OPTIONS]

Options:
  --path TEXT  Path to relations JSON files.
  --out TEXT   Path to save output file.
  --help       Show this message and exit.
"""

import os
import json
import re
import errno
from typing import Dict, List, Tuple

import click
import spacy
from spacy.symbols import *
from spacy.tokens import Token, Doc
from spacy import displacy

DEBUG = os.environ.get("DEBUG") == "true"

# use large model in production
LANG = "en_core_web_sm" if DEBUG else "en_core_web_lg"

# constants
SUBJECT = "SUBJECT"
OBJECT = "OBJECT"

# load spacy
try:
    nlp = spacy.load(LANG)
except OSError:
    print(
        "Downloading language model for the spaCy POS tagger\n"
        "(don't worry, this will only happen once)"
    )
    from spacy.cli import download

    download(LANG)
    nlp = spacy.load(LANG)


class Relation:
    def __init__(self, raw_sentence: str, subject: dict, object_: dict, relation_name: str):
        self.raw_sentence = raw_sentence.strip()
        self.subject = subject
        self.object = object_
        self.relation_name = relation_name
        self.entities = []
        self.normalized_sentence = None
        self.verbs = set()
        self.subject_paths = []
        self.object_paths = []
        self.shortest_path = set()  # (subject_path, object_path)

        # extract all labeled entities
        entities = self._extract_entities()
        # filter out subject and object
        cnt = 1
        for each in entities:
            if each["mid"] != self.subject["mid"] and each["mid"] != self.object["mid"]:
                self.entities.append({**each, "subst": "ENTITY{}".format(cnt)})
                cnt += 1
        # replace entities by ENTITYi
        sentence = self._subst_entities(self.raw_sentence)
        # rename subject/object by SUBJECT/OBJECT
        self.normalized_sentence = self._normalize_sentence(sentence)

    def __str__(self):
        return json.dumps(
            {
                "relation": self.relation_name,
                "normalized_sentence": self.normalized_sentence,
                "raw_sentence": self.raw_sentence,
                "verbs": [v.text for v in self.verbs],
                "subject_path": [[t.text for t in p] for p in self.subject_paths],
                "object_path": [[t.text for t in p] for p in self.object_paths],
                "entities": self.entities,
                "subject": self.subject,
                "object": self.object,
            },
            indent=2,
        )

    def __repr__(self):
        return str(
            {
                "relation": self.relation_name,
                "normalized_sentence": self.normalized_sentence,
                "raw_sentence": self.raw_sentence,
                "entities": self.entities,
                "subject": self.subject,
                "object": self.object,
            }
        )

    def __output__(self):
        subject_path = [[t.text for t in p] for p in self.subject_paths]
        object_path = [[t.text for t in p] for p in self.object_paths]
        output = """{}
{}
Subject Path: {}
Object Path: {}
Lowest common ancestor: {}""".format(
            self.normalized_sentence,
            self._entities_mapping(),
            str(subject_path),
            str(object_path),
            self.shortest_path[0][-1] if self.shortest_path else None,
        )
        return output

    def _entities_mapping(self):
        entities = [
            *self.entities,
            {**self.subject, "subst": SUBJECT},
            {**self.object, "subst": OBJECT},
        ]

        return "\n".join(
            [
                "{} - [[ {} | {} ]]".format(entity["subst"], entity["name"], entity["mid"])
                for entity in entities
            ]
        )

    def _extract_entities(self):
        matches = re.findall(r"\[\[ (.+?) \| (.+?) \]\]", self.raw_sentence)
        entities = []
        for i in range(len(matches)):
            entities.append({"name": matches[i][0], "mid": matches[i][1]})
        return entities

    def _normalize_sentence(self, sentence):
        # find left over labled entities
        matches = re.findall(r"\[\[ .+? \| .+? \]\]", sentence)

        for each in matches:
            tmp = re.search(r"\[\[ (.+?) \| (.+?) \]\]", each)
            if tmp.group(2) == self.subject["mid"]:
                sentence = sentence.replace(each, SUBJECT)
            elif tmp.group(2) == self.object["mid"]:
                sentence = sentence.replace(each, OBJECT)
            else:
                print("Opps, something is wrong. Double check sentence below.")
                print("{}: {}".format(self.relation_name, self.raw_sentence))

        return sentence

    def _subst_entities(self, sentence):
        for i in range(len(self.entities)):
            sentence = re.sub(
                "\[\[ {} \| {} \]\]".format(
                    re.escape(self.entities[i]["name"]), self.entities[i]["mid"]
                ),
                self.entities[i]["subst"],
                sentence,
            )
        return sentence

    def get_shortest_path_to_ancestors(self):
        """
        Get lowest common path to root for SUBJECT and OBJECT
        """
        if not self.object_paths or not self.subject_paths:
            return

        common_paths = []
        for i in self.subject_paths:
            for j in self.object_paths:
                if i[-1].text == j[-1].text:
                    common_paths.append((i, j))
        # find shortest
        if not common_paths:
            return

        lens_arr = [len(pair[0]) + len(pair[1]) for pair in common_paths]
        self.shortest_path = common_paths[lens_arr.index(min(lens_arr))]


def get_relations(dir="data") -> Dict[str, List[Relation]]:
    if not os.path.isdir(dir):
        raise Exception('Directory "{}" does not exist.'.format(dir))

    (dirpath, _, filenames) = next(os.walk(dir))
    filenames = sorted([filename for filename in filenames if filename.endswith(".json")])

    relations = {}
    for filename in filenames:
        with open(os.path.join(dirpath, filename)) as input_f:
            raw_data = json.load(input_f)
            relations[filename] = [
                Relation(
                    each["sentence"],
                    each["pair"]["subject"],
                    each["pair"]["object"],
                    each["relation"],
                )
                for each in raw_data
            ]
    return relations


# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# https://stackoverflow.com/a/23794010
def safe_open_w(path, mode="wt"):
    mkdir_p(os.path.dirname(path))
    return open(path, mode)


def save_output(relations, path="task2/runs/"):
    for filename, relations in relations.items():
        with safe_open_w(os.path.join(path, filename.replace(".json", ".txt")), "w") as output_f:
            buffer = "\n\n\n".join([r.__output__() for r in relations])
            output_f.write(buffer)


def get_paths_and_verbs(doc: Doc) -> Tuple[set, list, list]:
    """
    Get all paths from SUBJECT and OBJECT to root
    if root is a VERB
    """
    verbs = set()
    subject_path = []
    object_path = []

    for token in doc:
        if token.head.pos == VERB:
            verbs.add(token.head)

        # find path from object/subject back to
        if token.text == SUBJECT:
            subject_ancestors = [t for t in token.ancestors]
            if subject_ancestors and subject_ancestors[-1].pos == VERB:
                subject_ancestors.insert(0, token)
                subject_path.append(subject_ancestors)
        elif token.text == OBJECT:
            object_ancestors = [t for t in token.ancestors]
            if object_ancestors and object_ancestors[-1].pos == VERB:
                object_ancestors.insert(0, token)
                object_path.append(object_ancestors)

    return verbs, subject_path, object_path


@click.command()
@click.option("--path", default="data", help="Path to relations JSON files.")
@click.option("--out", default="task2/runs/", help="Path to save output file.")
def main(path="data", out="task2/runs"):
    all_relations = get_relations(dir=path)

    for relation_name, relations in all_relations.items():
        for relation in relations:
            doc = nlp(relation.normalized_sentence)
            relation.verbs, relation.subject_paths, relation.object_paths = get_paths_and_verbs(doc)
            relation.get_shortest_path_to_ancestors()

    save_output(all_relations, path=out)


if __name__ == "__main__":
    main()
    # text = {
    #     "sentence": "Pipeline gas connections Mahanagar Gas Limited  and [[ Indraprastha Gas Limited | /m/0gvv0z6 ]] , [[ Joint Venture | /m/02mz24 ]] companies of [[ GAIL (India) Limited | /m/02vzp1l ]] are supplying [[ Piped Natural Gas | /m/05k4k ]]  to 1.70 lakh...........................",
    #     "pair": {
    #         "subject": {"name": "Indraprastha Gas", "mid": "/m/0gvv0z6"},
    #         "object": {"name": "Natural gas", "mid": "/m/05k4k"},
    #     },
    #     "relation": "business.business_operation.industry",
    # }

    # relation = Relation(
    #     text["sentence"], text["pair"]["subject"], text["pair"]["object"], text["relation"]
    # )
    # print(relation)

    # doc = nlp(relation.normalized_sentence)
    # displacy.serve(doc, style="dep")
    # for each in doc:
    #     if each.text == SUBJECT:
    #         print([t for t in each.ancestors])
    #     elif each.text == OBJECT:
    #         print([t for t in each.ancestors])
    # relation.verbs, relation.subject_paths, relation.object_paths = get_paths_and_verbs(doc)
    # print(relation)
    # relation.get_shortest_path_to_ancestors()
    # print(relation.__output__())

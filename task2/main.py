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
import random
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
        self.lowest_common_ancestor = None
        self.subject_paths = []
        self.object_paths = []
        self.shortest_path = set()  # (subject_path, object_path)
        self._doc: Doc = None
        self._subject_idx = []
        self._object_idx = []

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
                "subject_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.subject_paths],
                "object_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.object_paths],
                "entities": self.entities,
                "subject": self.subject,
                "object": self.object,
                "lowest_common_ancestor": self._lowest_common_ancestor()
            },
            indent=2,
        )

    def __repr__(self):
        return str(
            {
                "relation": self.relation_name,
                "normalized_sentence": self.normalized_sentence,
                "raw_sentence": self.raw_sentence,
                "verbs": [v.text for v in self.verbs],
                "subject_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.subject_paths],
                "object_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.object_paths],
                "entities": self.entities,
                "subject": self.subject,
                "object": self.object,
                "lowest_common_ancestor": self._lowest_common_ancestor()
            }
        )

    def __json__(self):
        return {
                "relation": self.relation_name,
                "normalized_sentence": self.normalized_sentence,
                "raw_sentence": self.raw_sentence,
                "verbs": [v.text for v in self.verbs],
                "subject_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.subject_paths],
                "object_path": [["{}_{}".format(t.text, t.pos_) for t in p] for p in self.object_paths],
                "entities": self.entities,
                "subject": self.subject,
                "object": self.object,
                "lowest_common_ancestor": self._lowest_common_ancestor()
            }

    def __output__(self):
        subject_path = "\n".join(
            [
                "Subject Path: {}".format(" -> ".join(["{}_{}".format(t.text, t.pos_) for t in p]))
                for p in self.subject_paths
            ]
        )
        object_path = "\n".join(
            [
                "Object Path: {}".format(" -> ".join(["{}_{}".format(t.text, t.pos_) for t in p]))
                for p in self.object_paths
            ]
        )
        output = """{}
{}
{}
{}
Lowest common ancestor: {}""".format(
            self.normalized_sentence,
            self._entities_mapping(),
            str(subject_path),
            str(object_path),
            self._lowest_common_ancestor(),
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
            # extract mid from labled entities to match with subject/object
            # since name within the sentence is not consistent with metadata
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

    def _lowest_common_ancestor(self):
        lca_matrix = self._doc.get_lca_matrix();
        common_ancestor = set()
        for i in self._subject_idx:
            for j in self._object_idx:
                idx = lca_matrix[i][j]
                if idx != -1:
                    token: Token = self._doc[idx]
                    common_ancestor.add("{}_{}".format(token.text, token.pos_))

        return ", ".join(list(common_ancestor))

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


def save_output(all_relations, path="task2/runs/"):
    with safe_open_w(os.path.join(path, "output_full.json"), "w") as out_f:
        json.dump({k: [r.__json__() for r in relations] for k, relations in all_relations.items()}, out_f)

    relations_samples = {}
    for filename, relations in all_relations.items():
        random_sample = random.sample(relations, 100)
        relations_samples[filename] = random_sample
        with safe_open_w(os.path.join(path, filename.replace(".json", ".txt")), "w") as output_f:
            buffer = "\n\n\n".join([r.__output__() for r in random_sample])
            output_f.write(buffer)

    with safe_open_w(os.path.join(path, "output_samples.json"), "w") as out_f:
        json.dump({k: [r.__json__() for r in relations] for k, relations in relations_samples.items()}, out_f)


def get_paths_and_verbs(doc: Doc) -> Tuple[set, list, list]:
    """
    Get all paths from SUBJECT and OBJECT to root
    """
    verbs = set()
    subject_path = []
    object_path = []

    subject_idx = []
    object_idx = []
    cnt = 0
    for token in doc:
        if token.head.pos == VERB:
            verbs.add(token.head)

        # find path from object/subject back to
        if token.text == SUBJECT:
            subject_idx.append(cnt)
            subject_ancestors = [t for t in token.ancestors]
            if subject_ancestors:
                subject_ancestors.insert(0, token)
                subject_path.append(subject_ancestors)
        elif token.text == OBJECT:
            object_idx.append(cnt)
            object_ancestors = [t for t in token.ancestors]
            if object_ancestors:
                object_ancestors.insert(0, token)
                object_path.append(object_ancestors)
        cnt += 1
    return verbs, subject_path, object_path, subject_idx, object_idx


@click.command()
@click.option("--path", default="data", help="Path to relations JSON files.")
@click.option("--out", default="task2/runs/", help="Path to save output file.")
def main(path="data", out="task2/runs"):
    all_relations = get_relations(dir=path)

    for relation_name, relations in all_relations.items():
        for relation in relations:
            relation._doc = nlp(relation.normalized_sentence)
            relation.verbs, relation.subject_paths, relation.object_paths, relation._subject_idx, relation._object_idx = get_paths_and_verbs(
                relation._doc
            )

    save_output(all_relations, path=out)


if __name__ == "__main__":
    main()
    # text = {
    #     "sentence": "*In 1930 Mr. [[ Kellogg | /m/01l8vs ]] was given the [[ Nobel Peace Prize | /m/05f3q ]] for 1929, the prize for that year having been reserved.",
    #     "pair": {
    #         "subject": {"name": "Nobel Peace Prize", "mid": "/m/05f3q"},
    #         "object": {"name": "Frank B. Kellogg", "mid": "/m/01l8vs"},
    #     },
    #     "relation": "award.award_honor.award..award.award_honor.award_winner",
    # }

    # relation = Relation(
    #     text["sentence"], text["pair"]["subject"], text["pair"]["object"], text["relation"]
    # )
    # relation._doc = nlp(relation.normalized_sentence)
    # lca_matrix = relation._doc.get_lca_matrix()
    # relation.verbs, relation.subject_paths, relation.object_paths, relation._subject_idx, relation._object_idx = get_paths_and_verbs(
    #     relation._doc
    # )
    # print(relation.__output__())

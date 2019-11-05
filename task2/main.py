import os
import json
import re


class Relation:
    def __init__(self, raw_sentence: str, subject: dict, object_: dict, relation_name: str):
        self.raw_sentence = raw_sentence.strip()
        self.subject = subject
        self.object = object_
        self.relation_name = relation_name
        self.entities = []
        self.normalized_sentence = None

        # subst object and subject by OBJECT and SUBJECT
        self._normalize_sentence()
        # ectract a list of entities from normalized sentence
        self._extract_entities()

        if self.entities:
            # subst all entities with ENTITYi
            self._subst_entities()

    def __str__(self):
        return str({
            "relation": self.relation_name,
            "normalized_sentence": self.normalized_sentence,
            "entities": self.entities,
            "subject": self.subject,
            "object": self.object
        })

    def _extract_entities(self):
        matches = re.findall(r"\[\[ (.+?) \| (.+?) \]\]", self.normalized_sentence)

        for i in range(len(matches)):
            self.entities.append(
                {"name": matches[i][0], "mid": matches[i][1], "subst": "ENTITY{}".format(i + 1)}
            )

    def _normalize_sentence(self):
        tmp = re.sub(
            "\[\[ {} \| {} \]\]".format(self.subject["name"], self.subject["mid"]),
            # "\[\[ (.+?) \| {} \]\]".format(self.subject["mid"]),
            "SUBJECT",
            self.raw_sentence,
        )
        print(tmp)
        tmp = re.sub(
            "\[\[ {} \| {} \]\]".format(self.object["name"], self.object["mid"]),
            # "\[\[ (.+?) \| {} \]\]".format(self.object["mid"]),
            "OBJECT",
            tmp,
        )
        print(tmp)
        self.normalized_sentence = tmp

    def _subst_entities(self):
        for i in range(len(self.entities)):
            self.normalized_sentence = re.sub(
                "\[\[ {} \| {} \]\]".format(self.entities[i]["name"], self.entities[i]["mid"]),
                self.entities[i]["subst"],
                self.raw_sentence,
            )


def get_relations(dir="data") -> dict:
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


def main():
    relations = get_relations(dir="data")

    for relation_name, relation in relations.items():
        print(relation[0])


if __name__ == "__main__":
    # main()
    test = {
        "sentence": "First, I was asked to meet [[ Sooraj Barjatya | /m/026gbl_ ]] 's father [[ Raj Kumar Barjatya | /m/0jznp5 ]] ",
        "pair": {
            "subject": {
                "name": "Rajkumar Barjatya",
                "mid": "/m/0jznp5"
            },
            "object": {
                "name": "Sooraj Barjatya",
                "mid": "/m/026gbl_"
            }
        },
        "relation": "people.person.children"
    }
    print(Relation(test["sentence"], test["pair"]["subject"], test["pair"]["object"], test["relation"]))

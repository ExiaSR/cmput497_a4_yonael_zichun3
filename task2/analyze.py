import json
from collections import Counter

import spacy


nlp = spacy.load("en_core_web_lg")


def main():
    with open("task2/runs/output_samples.json", "r") as input_f:
        all_relations: dict = json.load(input_f)

        for relation_name, relations in all_relations.items():
            # count LCA
            lca_counter = Counter([r["lowest_common_ancestor"] for r in relations])

            # count LCA occurences that are VERB
            pos_tags_list = [
                r["lowest_common_ancestor"].split("_")[1]
                for r in relations
                if r["lowest_common_ancestor"]
            ]
            pos_counter = Counter(pos_tags_list)

            # count by LCA POS tag
            lca_verb = Counter(
                [
                    r["lowest_common_ancestor"]
                    for r in relations
                    if r["lowest_common_ancestor"]
                    and r["lowest_common_ancestor"].split("_")[1] == "VERB"
                ]
            )

            # count by LCA VERB tense
            words_list = [
                r["lowest_common_ancestor"] for r in relations if r["lowest_common_ancestor"]
            ]
            verbs_list = [w.split("_")[0] for w in words_list if w.split("_")[1] == "VERB"]
            lca_verb_stems = set([nlp(v)[0].lemma_ for v in verbs_list])

            print(relation_name)
            print(lca_counter)
            print(lca_verb)
            print(lca_verb_stems)
            print("Number of unique verb stems: {}".format(len(lca_verb_stems)))
            print(pos_counter)
            print("\n")


if __name__ == "__main__":
    main()

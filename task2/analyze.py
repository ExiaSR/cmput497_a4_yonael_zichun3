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

            # count by LCA VERB stem
            words_list = [
                r["lowest_common_ancestor"] for r in relations if r["lowest_common_ancestor"]
            ]
            verbs_list = [w.split("_")[0] for w in words_list if w.split("_")[1] == "VERB"]
            verbs_doc = [nlp(v)[0] for v in verbs_list]
            lca_verb_stems = set([nlp(v)[0].lemma_ for v in verbs_list])
            # count by LCA verb tense
            lca_verb_tense = [nlp.vocab.morphology.tag_map[v.tag_] for v in verbs_doc]
            lca_verb_tense_count = Counter(['Tense_past' if v.get('Tense_past', False) else 'Tense_pres' for v in lca_verb_tense])

            print(relation_name)
            print("All LCA: {}".format(lca_counter))
            print("LCA verbs: {}".format(lca_verb))
            print("Number of LCA that are verb: {}".format(sum(lca_verb.values())))
            print("LCA verbs stems: {}".format(lca_verb_stems))
            print("Number of unique verb stems: {}".format(len(lca_verb_stems)))
            print("LCA verbs tense count: {}".format(lca_verb_tense_count))
            print("LCA POS tag count: {}".format(pos_counter))
            print("\n")


if __name__ == "__main__":
    main()

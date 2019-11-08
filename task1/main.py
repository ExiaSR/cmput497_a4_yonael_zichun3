import click
import sys
import os
import logging
import json 
import re

import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()

logger = logging.getLogger("cmput497")

class MisIdent:
    def __init__(self, relations):
        self.relations = relations 
        # tuple of sentence, tokens
        self.cleaned_sentences = {}
    
    def run(self):
        self.clean_sentences()
        self.tag()
 

    # cleans the sentences of the free base tokens 
    def clean_sentences(self):
        # goes through files and gets all the relation sentences
        for fn in self.relations.keys():
            sentences = self.relations[fn]
            cleaned_sentences = []
            # goes through all the relation sentences and cleans them 
            for sent in sentences:
                clean_sent = sent 
                freebase_tokens = re.findall(r'(?<=\[)(.*?)(?=\|)', sent)
                full_tokens = re.findall(r'(\[.*?\]])', sent)
                cleaned_tokens = self.clean_tokens(freebase_tokens)

                # goes through all tokens and replaces instance in the original sentence 
                for i in range(len(full_tokens)):
                    clean_sent = clean_sent.replace(full_tokens[i], cleaned_tokens[i]).strip()
            
                cleaned_sentences.append((clean_sent, cleaned_tokens))
            self.cleaned_sentences[fn] = cleaned_sentences
    
    # tags the cleaned sentences using spaCy's POS tagger
    def tag(self):
        for fn in self.cleaned_sentences.keys():
            filename = 'task1/runs/{}.txt'.format(fn)
            # opens the file to show output of sentence, words with tags and incorrect identification 
            with open(filename, "w+") as f: 
                filtered_sentences = 0
                mistagged_sentences = 0 
                sentences = self.cleaned_sentences[fn]
                for sent in sentences:
                    # sometimes there are two mistakes in one sentence. we should just count it once
                    doc = nlp(sent[0])
                    mistagged = []
                    tagged = []
                    for token in doc:
                        if ((token.text in sent[1]) and (token.tag_[0] != 'N')):
                            mistagged.append((token.text, token.tag_))
                        
                        else:
                            tagged.append((token.text, token.tag_))

                    if (len(mistagged) > 0):
                        f.write("{}".format(sent[0]))
                        for tag in tagged:
                            f.write("\n{} {}".format(tag[0], tag[1]))
                        for mistag in mistagged:
                            f.write("\n{} {} Incorrect".format(mistag[0], mistag[1]))
                            mistagged_sentences += 1
                        filtered_sentences += 1
                        
                        f.write('\n')
                        f.write('\n')
                        f.write('\n')

            #  opens the file to show the statistics
            with open("task1/stats/"+fn+"_stats.txt", "w+") as f2: 
                f2.write("{} had {} filtered sentences".format(fn, filtered_sentences))
                f2.write("{} had {} mistagged entities".format(fn, mistagged_sentences))

    #https://stackoverflow.com/questions/37192606/python-regex-how-to-delete-all-matches-from-a-string
   # cleans the tokens of the whitespace and freebase characters
    def clean_tokens(self, rgx_list):
        clean_list = []
        for token in rgx_list:
            new_tok = token[1:len(token)].strip()
            clean_list.append(new_tok)

        return clean_list

# goes through json code and extracts all the sentences and enters them in dictionary (KEY = Filename)
def get_relations(dir="data"):
    if not os.path.isdir(dir):
        raise Exception('Directory "{}" does not exist.'.format(dir))

    (dirpath, _, filenames) = next(os.walk(dir))
    filenames = sorted([filename for filename in filenames if filename.endswith(".json")])

    relations = {}
    for filename in filenames:
        with open(os.path.join(dirpath, filename)) as input_f:
            raw_data = json.load(input_f)
            sentences = []
            for i in raw_data:
                sentences.append(i['sentence'])
            relations[filename] = sentences

    return relations

def main():
    relations = get_relations(dir="data")
    misIdent = MisIdent(relations) 
    misIdent.run()
    
main()
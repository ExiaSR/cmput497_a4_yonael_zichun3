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
    def __init__(self, raw_data=[], sentences=[], relations=[]):
        self.raw_data = raw_data
        self.relations = relations
        self.sentences = sentences 
        self.cleaned_sentences = []


    def clean_sentences(self):
        for sent in self.sentences:
            clean_sent = sent 
            freebase_tokens = re.findall(r'(?<=\[)(.*?)(?=\|)', sent)
            full_tokens = re.findall(r'(\[.*?\]])', sent)
            cleaned_tokens = self.clean_tokens(freebase_tokens)

            for i in range(len(full_tokens)):
                clean_sent = clean_sent.replace(full_tokens[i], cleaned_tokens[i]).strip()
        
            self.cleaned_sentences.append(clean_sent)

            noun_phrases = self.tagger(clean_sent)
            for tok in cleaned_tokens:
                exist = 0
                for np in noun_phrases:
                   
                    # checks if substring of token is in noun phrases
                    if tok in np:
                        exist = 1
                    
                    # checks if substring of np is in token
                    elif np in tok: 
                        exist = 1
                
                if exist != 1: 
                    print("The token = {} \nis a misidentified noun in \n{}".format(tok, sent))

            # print("These are the noun phrases = {}".format(noun_phrases))
            # print("These are the tagged entities = {}".format(cleaned_tokens))
    
    #https://stackoverflow.com/questions/48925328/how-to-get-all-noun-phrases-in-spacy
    def tagger(self, sentence): 
        doc = nlp(sentence)
        noun_phrases = []
        for np in doc.noun_chunks:
            noun_phrases.append(np.text)

        return noun_phrases
    
    #https://stackoverflow.com/questions/37192606/python-regex-how-to-delete-all-matches-from-a-string
   # cleans the tokens of the whitespace and freebase characters
    def clean_tokens(self, rgx_list):
        clean_list = []
        for token in rgx_list:
            new_tok = token[1:len(token)].strip()
            clean_list.append(new_tok)

        return clean_list

# TODO : Go through all 
def get_relations(dir="data") -> dict:
        if not os.path.isdir(dir):
            raise Exception('Directory "{}" does not exist.'.format(dir))

        (dirpath, _, filenames) = next(os.walk(dir))
        filenames = sorted([filename for filename in filenames if filename.endswith(".json")])

        data = {}
        for filename in filenames:
            with open(os.path.join(dirpath, filename)) as input_f:
                raw_data = json.load(input_f) 
                sentences = []
                relations = []

                for i in raw_data:
                    sentences.append(i['sentence'])
                    relations.append(i['pair'])

                # raw data is the Raw JSON, Sentences is all the sentences, pairs is the relations 
                return raw_data, sentences, relations
    
def main():
    raw_data, sentences, relations = get_relations(dir="data")
    misIdent = MisIdent(raw_data, sentences, relations) 
    misIdent.clean_sentences()
    


main()
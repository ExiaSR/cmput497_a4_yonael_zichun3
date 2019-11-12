import click
import sys
import os
import errno
import logging
import json 
import re

import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
nlp = en_core_web_sm.load()

logger = logging.getLogger("cmput497")

def main():
    data_files = get_data_files()
    all_content = []
   
    #test = []
    for f in data_files: 
        content = read_file(f)
        track_misid(content)
        # for i in content: 
        #     test = (i['sentence'])
        # print(test)
        all_content.append(content)
    
def track_misid(phrases):
    for sent in phrases:
        freebase_tokens = re.findall(r'\[(.*?)\]]', sent['sentence'])
        cleaned_sent = clean_text(freebase_tokens, sent['sentence'])
        print(cleaned_sent)
    

#https://stackoverflow.com/questions/37192606/python-regex-how-to-delete-all-matches-from-a-string
def clean_text(rgx_list, text):
    new_text = text
    for rgx_match in rgx_list:
        new_text = re.sub(rgx_match, ' ', new_text).rstrip()

    #TODO fix the unterminated character set at position 0

    # TODO once clean check NER 
    return new_text


    
    
    


def get_data_files():
    filenames = []
    for file in os.listdir("data"):
        if file.endswith(".json"):
            filenames.append(file)
    
    return filenames 

def read_file(filename): 
    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    rel_path = "data/"+filename
    abs_file_path = os.path.join(script_dir, rel_path)
    with open(abs_file_path, 'r') as f:
        content = json.load(f)
        
        
    
    return content


main()
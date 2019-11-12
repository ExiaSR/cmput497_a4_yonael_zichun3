## Task 1

### How to run

**Execute program from root directory**

```sh
# small model for development
$ python -m spacy download en_core_web_sm

# will output files under task1/runs. Will have "Incorrect" next to all the misclassifications
$ python task1/main.py

# for additional statistics
**note that under task1/stats will be statistics every file analyzed with the # of filtered sentences and mistagged entities.


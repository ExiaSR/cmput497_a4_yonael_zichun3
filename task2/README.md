## Task 2

### How to run

**Execute program from root directory**

```sh
# small model for development
$ python -m spacy download en_core_web_sm

# larger model for final submission and anlysis
$ python -m spacy download en_core_web_lg

# DEBUG=true to use a smaller lanaguage model to test
$ python task2/main.py

# get some statistic of the random samples
$ python task2/analyze.py > sample_report.txt
```

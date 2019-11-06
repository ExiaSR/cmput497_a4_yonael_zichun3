import os
import random
import errno


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


def random_sample(dir="task2/runs/", out="task2/samples"):
    if not os.path.isdir(dir):
        raise Exception('Directory "{}" does not exist.'.format(dir))

    (dirpath, _, filenames) = next(os.walk(dir))
    filenames = sorted([filename for filename in filenames if filename.endswith(".txt")])

    relations = {}
    for filename in filenames:
        with open(os.path.join(dirpath, filename)) as input_f, safe_open_w(
            os.path.join(out, filename)
        ) as output_f:
            sentences = input_f.read().split("\n\n\n")
            samples = random.sample(sentences, 100)
            output_f.write("\n\n\n".join(samples))


if __name__ == "__main__":
    random_sample()

#!/usr/bin/python

import pep8
from os.path import abspath, dirname


class options:
    filename = ["*.py"]
    exclude = ".hg"
    verbose = False
    counters = {}
    messages = {}
    testsuite = False
    quiet = False
    ignore = []
    repeat = False
    show_source = True
    show_pep8 = False


def main():
    """
    Parse options and run checks on Python source.
    """
    pep8.options = options()
    repo = dirname(dirname(abspath(__file__)))
    pep8.input_dir(repo)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3 

import shutil
import glob
import os
import argparse
import sys

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", metavar="DATASET NAME", help="the dataset whos out_* files to move")

    inps = parser.parse_args(sys.argv[1:])

    return inps

if __name__ == "__main__":

    inps = create_parser()

    os.chdir(os.getenv("SCRATCHDIR")+"/"+inps.dataset)

    files = glob.glob("out_*")

    for filename in files:

        base = os.getenv('OPERATIONS') + '/OUT_FILES/' + inps.dataset + '/'

        if not os.path.exists(base):
            os.makedirs(base)

        dest = base + filename

        shutil.move(os.getcwd()+"/"+filename, dest)

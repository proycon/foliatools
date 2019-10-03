#!/usr/bin/env python

"""
This is a benchmarking tool for the foliapy library.
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import argparse
import time
import gc
import resource
from foliatools import VERSION as TOOLVERSION
import folia.main as folia

ansicolors = {"red":31,"green":32,"yellow":33,"blue":34,"magenta":35, "bold":1 }
def colorf(color, x):
    return "\x1B[" + str(ansicolors[str(color)]) + "m" + x + "\x1B[0m"


def getmem():
    rusage_denom = 1024.
    if sys.platform == 'darwin':
        # ... it seems that in OSX the output is different units ...
        rusage_denom = rusage_denom * rusage_denom
    mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / rusage_denom
    return mem

def begin():
    gc.collect()
    return time.time(), getmem()

def end(data):
    begintime, beginmem = data
    d = (time.time() - begintime)
    d = d * 1000
    memd = getmem() - beginmem
    gc.collect()
    return d, memd


def run_test(test_id, file):
    if test_id == 'parse':
        title = "Parse XML from file into full memory representation"
        begintime, beginmem = begin()
        doc = folia.Document(file=file)
        return begintime, beginmem, title , doc
    elif test_id == 'serialise':
        title = "Serialise to XML"
        doc = folia.Document(file=file)
        begintime, beginmem = begin()
        out = doc.xmlstring()
        return begintime, beginmem, title , out
    elif test_id == 'text':
        title = "Serialise to text"
        doc = folia.Document(file=file)
        begintime, beginmem = begin()
        out = doc.text()
        return begintime, beginmem, title , out
    elif test_id == 'select':
        title = "Select all words"
        doc = folia.Document(file=file)
        begintime, beginmem = begin()
        for word in doc.select(folia.Word):
            pass
        return begintime, beginmem, title, None
    raise KeyError("No such test: " + test_id)

def test(test_id,file, args):
    times = []
    mems = []
    title = ""
    for i in range(0,args.iterations):
        begintime, beginmem, title, doc = run_test(test_id,file)
        t, mem  = end((begintime, beginmem))
        times.append(t)
        mems.append(mem)
    t = sum(times) / float(len(times))
    mem = sum(mems) / float(len(mems))
    print(file +  " - [" + test_id+ "] " + title + ": " + colorf('yellow',str(round(t,3))+ 'ms') + " -- Memory: " + colorf('green',str(round(mem,2))+ ' MB') + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('-i','--iterations', type=int,help="Number of iterations to run and average over", action='store',default=1,required=False)
    parser.add_argument('-t','--tests', type=str,help="Comma separated list of test IDs", action='store',default="parse,serialise,text,words",required=False)
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to validate')
    args = parser.parse_args()

    for file in args.files:
        for test_id in args.tests.split(","):
            test(test_id, file, args)


if __name__ == '__main__':
    main()


#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
Assigns unique identifiers to structural elements within a FoLiA document where there are none yet
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import getopt
import io
import sys
import os
import glob
from collections import Counter
import folia.main as folia
from foliatools import VERSION as TOOLVERSION

def usage():
    print("foliaid",file=sys.stderr)
    print("  by Maarten van Gompel (proycon)",file=sys.stderr)
    print("  Centre for Language and Speech Technology, Radboud University Nijmegen",file=sys.stderr)
    print("  2017-2019 - Licensed under GPLv3",file=sys.stderr)
    print("",file=sys.stderr)
    print(__doc__, file=sys.stderr)
    print("",file=sys.stderr)
    print("Usage: foliaid [options] file-or-dir1 file-or-dir2 ..etc..",file=sys.stderr)
    print("",file=sys.stderr)
    print("Parameters for processing directories:",file=sys.stderr)
    print("  -r                           Process recursively",file=sys.stderr)
    print("  -E [extension]               Set extension (default: xml)",file=sys.stderr)
    print("  -t [types]                   Output only these elements (comma separated list)", file=sys.stderr)
    print("  -P                           Like -O, but outputs to current working directory",file=sys.stderr)
    print("  -q                           Ignore errors",file=sys.stderr)

def out(s, outputfile):
    if sys.version < '3':
        if outputfile:
            outputfile.write(s + "\n")
        else:
            print(s.encode(settings.encoding))
    else:
        if outputfile:
            print(s,file=outputfile)
        else:
            print(s)


def process(filename, outputfile = None):
    print("Processing " + filename,file=sys.stderr)
    try:
        doc = folia.Document(file=filename,keepversion=True)
        processor = folia.Processor.create(name="foliaid",version=TOOLVERSION)
        assignids(doc, settings.types, True)
        doc.provenance.append(processor)
    except Exception as e:
        if settings.ignoreerrors:
            print("ERROR: An exception was raised whilst processing " + filename + ":", e, file=sys.stderr)
        else:
            raise

    doc.save()

def assignids(doc, types=None, verbose=False):
    for e in doc.data:
        if e.id is None:
            e.id = doc.id + '.' + e.XMLTAG + '.1'
            doc[e.id] = e
            if verbose: print(" /-> ", e.id,file=sys.stderr)

    for e in doc.select(folia.AbstractStructureElement):
        if e.id is None and not isinstance(e, (folia.Linebreak, folia.Whitespace)):
            if not types or e.XMLTAG in types:
                parent = e.parent
                while not parent.id:
                    parent = parent.parent
                try:
                    e.id = parent.generate_id(e.__class__)
                except folia.GenerateIDException:
                    if verbose: print(repr(e), repr(parent), parent.id, file=sys.stderr)
                    raise
                if verbose: print(" --> ", e.id,file=sys.stderr)




def processdir(d, outputfile = None):
    print("Processing directory  " + d, file=sys.stderr)
    for f in glob.glob(os.path.join(d, '*')):
        if f[-len(settings.extension) - 1:] == '.' + settings.extension:
            process(f, outputfile)
        elif settings.recurse and os.path.isdir(f):
            rocessdir(f, outputfile)


class settings:
    extension = 'xml'
    recurse = False
    ignoreerrors = False
    types = None


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:OPE:ht:spwrq", ["help"])
    except getopt.GetoptError as err:
        print(str(err), file=sys.stderr)
        usage()
        sys.exit(2)


    outputfile = None


    for o, a in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        elif o == '-E':
            settings.extension = a
        elif o == '-r':
            settings.recurse = True
        elif o == '-t':
            settings.types = a.split(',')
        elif o == '-q':
            settings.ignoreerrors = True
        else:
            raise Exception("No such option: " + o)


    if outputfile: outputfile = io.open(outputfile,'w',encoding=settings.encoding)

    if args:
        for x in args:
            if os.path.isdir(x):
                processdir(x,outputfile)
            elif os.path.isfile(x):
                process(x, outputfile)
            else:
                print("ERROR: File or directory not found: " + x, file=sys.stderr)
                sys.exit(3)

    else:
        print("ERROR: Nothing to do, specify one or more files or directories", file=sys.stderr)



if __name__ == "__main__":
    main()

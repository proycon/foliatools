#!/usr/bin/env python
# -*- coding: utf8 -*-

"""Concatenates two or more FoLiA documents"""

from __future__ import print_function, unicode_literals, division, absolute_import

import argparse
import sys
from foliatools import VERSION as TOOLVERSION
import folia.main as folia


def concat(target, source):
    merges = 0
    for e in source:
        c = e.copy(target.doc)
        target.append(c)
        merges += 1
    return merges



def foliacat(id, outputfile, *files, keepversion=True):
    totalmerges = 0
    processor = folia.Processor.create(name="foliacat",version=TOOLVERSION)
    outputdoc = folia.Document(id=id,keepversion=keepversion, processor=processor, declare=[]) #do not predeclare anything
    if keepversion:
        outputdoc.version = "0.0.0"
    text = outputdoc.append(folia.Text(outputdoc,id=id + ".text"))
    for i, filename in enumerate(files):
        merges = 0
        print("Processing " + filename, file=sys.stderr)
        inputdoc = folia.Document(file=filename,keepversion=True)
        #we take the version of the newest document
        if keepversion:
            if folia.checkversion(inputdoc.version, outputdoc.version) > 0:
                outputdoc.version = inputdoc.version
                outputdoc.FOLIA2 = folia.checkversion(outputdoc.version, "2.0.0") >= 0
                outputdoc.FOLIA1 = folia.checkversion(outputdoc.version, "2.0.0") < 0

        print("(concatenating document)",file=sys.stderr)

        for annotationtype,set in inputdoc.annotations:
            if not outputdoc.declared(annotationtype,set):
                print("Declaring " + folia.annotationtype2str(annotationtype), repr(set), file=sys.stderr)
                outputdoc.declare( annotationtype, set)

        for d in inputdoc.data:
            merges += concat(text, d)

        print("(concatenating " + str(merges) + " elements, with all elements contained therein)",file=sys.stderr)
        totalmerges += merges


    print("(TOTAL: concatenated " + str(totalmerges) + " elements, with all elements contained therein)",file=sys.stderr)
    if outputfile and merges > 0:
        outputdoc.save(outputfile)

    return outputdoc

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('-i','--id',type=str, help="Set the ID for the output document", action='store', required=True)
    parser.add_argument('-o','--output',type=str, help="Output file (defaults to stdout if not set)", required=True)
    parser.add_argument('-u','--upgrade', help="Automatically upgrade FoLiA version to the latest version, warning: make sure you validate your document afterwards as this does not always work!", action='store_true')
    parser.add_argument('files', nargs='*', help='Files to concatenate')
    args = parser.parse_args()

    if len(args.files) < 2:
        print("WARNING: only one file specified", file=sys.stderr)


    outputdoc = foliacat(args.id, args.output, *args.files, keepversion=not args.upgrade)
    if not args.output or args.output == '-':
        print(outputdoc.xmlstring())

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf8 -*-

"""Erase the specified annotation types from a FoLiA document, effectively simplifying the document"""

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



def foliaerase(filename, erasetypes, keepversion=True):
    print("Processing " + filename, file=sys.stderr)
    doc = folia.Document(file=filename, keepversion=keepversion)
    if not keepversion or folia.checkversion(doc.version, "2.0.0") >= 0:
        processor = folia.Processor.create(name="foliaerase",version=TOOLVERSION)
        doc.provenance.append(processor)
    for Class, annotationset in erasetypes:
        count = doc.erase(Class, annotationset)
        print(f"Removed {count} annotations of type {Class.XMLTAG} and set {annotationset}",file=sys.stderr)
    return doc

def parsetype(s):
    if s.lower() in folia.XML2CLASS:
        return folia.XML2CLASS[s]
    try:
        return folia.XML2CLASS[folia.ANNOTATIONTYPE2XML[folia.str2annotationtype(s)]]
    except KeyError:
        raise ValueError("No such annotation type: " + s)

def parsetypes(s):
    pairs = s.split(";")
    for pair in pairs:
        pair = pair.strip()
        if ',' in pair:
            t, s = pair.split(',')
            yield (parsetype(t.strip()), s)
        else:
            yield (parsetype(pair.strip()), False)

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('-n','--dryrun', help="Do not write files", action='store_true')
    parser.add_argument('-O','--output', help="Output to standard output", action='store_true')
    parser.add_argument('-u','--upgrade', help="Automatically upgrade FoLiA version to the latest version, warning: make sure you validate your document afterwards as this does not always work for large upgrades! Preferably use the foliaupgrade tool instead", action='store_true')
    parser.add_argument('-t','--types', type=str, help="Annotation types to erase. This is a semicolon separated list of annotation types (you can use the primary FoLiA XML tags), set names are separated from the annotation type by a comma.", required=True )
    parser.add_argument('files', nargs='*', help='Files to process')
    args = parser.parse_args()

    if len(args.files) < 1:
        print("No files specified! Do --help for usage info!", file=sys.stderr)

    for file in args.files:
        doc = foliaerase(file, parsetypes(args.types), keepversion=not args.upgrade)
        if not args.dryrun:
            doc.save()
        if args.output:
            print(doc.xmlstring())

if __name__ == "__main__":
    main()

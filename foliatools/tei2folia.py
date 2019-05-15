#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#---------------------------------------------------------------
# TEI to FoLiA Converter
#   by Maarten van Gompel
#   Centre for Language Studies
#   Radboud University Nijmegen
#   proycon AT anaproy DOT nl
#
#   Licensed under GPLv3
#
# This script converts *SOME VARIANTS* of TEI to the FoLiA format.
# Because of the great diversity in TEI formats, it is not
# guaranteed to work in all circumstances.
#
#----------------------------------------------------------------

import lxml.etree
import argparse
import folia.main as folia

def convert(filename, **args):
    teidoc = lxml.etree.parse(filename).getroot()
        if node.tag.startswith('{' + NSTEI + '}'):
    for element in doc:
        #element.tag, element.attrib['blah'], element.text
    for element in doc.xpath("//test"):
        pass

def parsetei(node):
    if isinstance(node,ElementTree._ElementTree): #pylint: disable=protected-access
        node = node.getroot()


def main():
    parser = argparse.ArgumentParser(description="Convert *SOME VARIANTS* of TEI to FoLiA XML. Because of the great diversity in TEI formats, it is not guaranteed to work in all circumstances.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory", action="store",default=".",required=False)
    parser.add_argument('files', nargs='+', help='TEI Files to process')
    args = parser.parse_args()
    #args.storeconst, args.dataset, args.num, args.bar
    for filename in args.files:
        doc = convert(filename, **args)


if __name__ == '__main__':
    main()


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

import sys
import argparse
import os.path
import lxml.etree
import traceback
from socket import getfqdn
from datetime import datetime
from foliatools import VERSION as TOOLVERSION
import folia.main as folia
import foliatools.xslt as xslt

def convert(filename, transformer, **kwargs):
    if not os.path.exists(filename):
        raise Exception("File not found: " + filename)
    begindatetime = datetime.now()
    parsedsource = lxml.etree.parse(filename)
    transformed = transformer(parsedsource)
    try:
        doc = folia.Document(tree=transformed)
    except folia.DeepValidationError as e:
        print("DEEP VALIDATION ERROR on full parse by library in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        return False
    except Exception as e:
        print("VALIDATION ERROR on full parse by library in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        if kwargs.get('traceback') or kwargs.get('debug'):
            print("-- Full traceback follows -->",file=sys.stderr)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_exception(ex_type, ex, tb)
        return False
    if doc.textvalidationerrors:
        print("VALIDATION ERROR because of text validation errors, in " + filename,file=sys.stderr)
        return False
    #augment the processor added by the above XSL stylesheet
    doc.provenance.processors[-1].version = TOOLVERSION
    doc.provenance.processors[-1].host = getfqdn()
    try:
        executable = os.path.basename(sys.argv[0])
        doc.provenance.processors[-1].command = " ".join([executable] + sys.argv[1:])
    except:
        pass
    doc.provenance.processors[-1].begindatetime = begindatetime
    doc.provenance.processors[-1].enddatetime = datetime.now()
    doc.provenance.processors[-1].folia_version = folia.FOLIAVERSION
    if 'USER' in os.environ:
        doc.provenance.processors[-1].user = os.environ['USER']
    #add subprocessor for validation
    doc.provenance.processors[-1].append( folia.Processor.create(name="foliavalidator", version=TOOLVERSION, src="https://github.com/proycon/foliatools", metadata={"valid": "yes"}) )
    return doc


def loadxslt():
    xsldir = os.path.dirname(__file__)
    if xsltfilename[0] != '/': xsltfilename = os.path.join(xsldir, xsltfilename)
    if not os.path.exists(xsltfilename):
        raise Exception("XSL Stylesheet not found: " + xsltfilename)
    xslt = lxml.etree.parse(xsltfilename)
    transformer = lxml.etree.XSLT(xslt)
    return transformer


def main():
    parser = argparse.ArgumentParser(description="Convert *SOME VARIANTS* of TEI to FoLiA XML. Because of the great diversity in TEI formats, it is not guaranteed to work in all circumstances.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory", action="store",default=".",required=False)
    parser.add_argument('-D','--debug',type=int,help="Debug level", action='store',default=0)
    parser.add_argument('-b','--traceback',help="Provide a full traceback on validation errors", action='store_true', default=False)
    parser.add_argument('files', nargs='+', help='TEI Files to process')
    args = parser.parse_args()
    for filename in args.files:
        doc = convert(filename, loadxslt(), **args.__dict__)


if __name__ == '__main__':
    main()


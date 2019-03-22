#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys
import os
import glob
import traceback
import lxml.etree
import argparse
from foliatools import VERSION as TOOLVERSION
import folia.main as folia


def validate(filename, schema = None,**kwargs):
    try:
        folia.validate(filename, schema)
    except Exception as e:
        print("VALIDATION ERROR against RelaxNG schema (stage 1/2), in " + filename,file=sys.stderr)
        print(str(e), file=sys.stderr)
        return False
    try:
        document = folia.Document(file=filename, deepvalidation=kwargs.get('deep',False),textvalidation=kwargs.get('stricttextvalidation',False),verbose=True, autodeclare=kwargs.get('autodeclare',False), debug=kwargs.get('debug'))
    except folia.DeepValidationError as e:
        print("DEEP VALIDATION ERROR on full parse by library (stage 2/2), in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        return False
    except Exception as e:
        print("VALIDATION ERROR on full parse by library (stage 2/2), in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        if kwargs.get('traceback') or kwargs.get('debug'):
            print("-- Full traceback follows -->",file=sys.stderr)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_exception(ex_type, ex, tb)
        return False
    if not document.version:
        print("VALIDATION ERROR: Document does not advertise FoLiA version (" + filename + ")",file=sys.stderr)
        return False
    elif folia.checkversion(document.version) == -1 and not kwargs.get('nowarn'):
        if document.version.split('.')[0] in ('0','1'):
            print("WARNING: Document (" + filename + ") uses an older FoLiA version ("+document.version+") but is validated with a newer library (" + folia.FOLIAVERSION+"). If this is a document you created and intend to publish, you may want to upgrade this FoLiA v1 document to FoLiA v2 using the 'foliaupgrade' tool.",file=sys.stderr)
        else:
            print("WARNING: Document (" + filename + ") uses an older FoLiA version ("+document.version+") but is validated according to the newer specification (" + folia.FOLIAVERSION+"). You might want to increase the version attribute if this is a document you created and intend to publish.",file=sys.stderr)
    if document.textvalidationerrors:
        if kwargs.get('stricttextvalidation'):
            print("VALIDATION ERROR because of text validation errors, in " + filename,file=sys.stderr)
            return False
        elif not kwargs.get('nowarn'):
            print("WARNING: there were " + str(document.textvalidationerrors) + " text validation errors but these are currently not counted toward the full validation result (use -t for strict text validation)", file=sys.stderr)

    if kwargs.get('output'):
        print(document.xmlstring())
    if kwargs.get('autodeclare'):
        print("Validated successfully **after** applying auto-declarations: " +  filename,file=sys.stderr)
        return document
    else:
        print("Validated successfully: " +  filename,file=sys.stderr)
        return True




def processdir(d, schema = None, **kwargs):
    success = False
    print("Searching in  " + d,file=sys.stderr)
    extension = kwargs.get('extension','xml').strip('.')
    for f in glob.glob(os.path.join(d ,'*')):
        r = True
        if f[-len(extension) - 1:] == '.' + extension:
            r = validate(f, schema,**kwargs)
        elif kwargs.get('recurse') and os.path.isdir(f):
            r = processdir(f,schema,**kwargs)
        if not r: success = False
    return success

def commandparser(parser):
    parser.add_argument('-d','--deep',help="Enable deep validation; validated uses classes against provided set definitions", action='store_true', default=False)
    parser.add_argument('-r','--recurse',help="Process recursively", action='store_true', default=False)
    parser.add_argument('-a','--autodeclare',help="Attempt to automatically declare missing annotations", action='store_true', default=False)
    parser.add_argument('-q','--quick',help="Quick and more shallow validation, only validates against RelaxNG schema. This does not constitute a complete enough validation!", action='store_true', default=False)
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml")
    parser.add_argument('-W','--nowarn',help="Suppress warnings", action='store_true', default=False)
    parser.add_argument('-i','--ignore',help="Always report a successful exit code, even in case of validation errors", action='store_true', default=False)
    parser.add_argument('-t','--stricttextvalidation',help="Treat text validation errors strictly (recommended and default for FoLiA v1.5+)", action='store_true', default=False)
    parser.add_argument('-o','--output',help="Output document to stdout", action='store_true', default=False)
    parser.add_argument('-D','--debug',type=int,help="Debug level", action='store',default=0)
    parser.add_argument('-b','--traceback',help="Provide a full traceback on validation errors", action='store_true', default=False)
    return parser

def main():
    parser = argparse.ArgumentParser(description="Checks whether a FoLiA document is a valid FoLiA document, i.e. whether it properly adheres to the FoLiA specification. Invalid documents should never be used or published.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    commandparser(parser)
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to validate')
    args = parser.parse_args()

    schema  = lxml.etree.RelaxNG(folia.relaxng())

    if args.files:
        success = True
        skipnext = False
        for file in args.files:
            r = False
            if os.path.isdir(file):
                r = processdir(file,schema, **args.__dict__)
            elif os.path.isfile(file):
                r = validate(file, schema, **args.__dict__)
            else:
                print("ERROR: File or directory not found: " + file,file=sys.stderr)
                sys.exit(3)
            if not r: success= False
        if not success and not args.ignore:
            sys.exit(1)
    else:
        print("ERROR: No files specified. Add --help for usage details.",file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()

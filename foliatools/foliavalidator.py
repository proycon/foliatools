#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
Checks whether a FoLiA document is a valid FoLiA document, i.e. whether it properly adheres to the FoLiA specification. Invalid documents should never be used or published. This tool is one of the most indispensable tools in the toolbox for anyone dealing with FoLiA.
"""

import sys
import os
import glob
import traceback
import lxml.etree
import argparse
from foliatools import VERSION as TOOLVERSION
import folia.main as folia


def validate(filename, schema = None,**kwargs):
    if not kwargs.get('quick'):
        try:
            folia.validate(filename, schema)
        except Exception as e:
            print("VALIDATION ERROR against RelaxNG schema (stage 1/3), in " + filename,file=sys.stderr)
            print(str(e), file=sys.stderr)
            return False
    try:
        document = folia.Document(file=filename, deepvalidation=kwargs.get('deep',False),textvalidation=kwargs.get('stricttextvalidation',False),verbose=True, autodeclare=kwargs.get('autodeclare',False), processor=kwargs.get('processor'), keepversion=kwargs.get('keepversion'), fixunassignedprocessor=kwargs.get('fixunassignedprocessor'), debug=kwargs.get('debug',0))
    except folia.DeepValidationError as e:
        print("DEEP VALIDATION ERROR on full parse by library (stage 2/3), in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        return False
    except Exception as e:
        print("VALIDATION ERROR on full parse by library (stage 2/3), in " + filename,file=sys.stderr)
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
            print("VALIDATION ERROR because of text validation errors (stage 2/3), in " + filename,file=sys.stderr)
            return False
        elif not kwargs.get('nowarn'):
            print("WARNING: there were " + str(document.textvalidationerrors) + " text validation errors but these are currently not counted toward the full validation result (use -t for strict text validation)", file=sys.stderr)
    if not kwargs.get('quick'):
        try:
            if kwargs.get('output'):
                if not (folia.checkversion(document.version, "2.0.0") < 0 and kwargs.get('keepversion')):
                    document.provenance.append( folia.Processor.create(name="foliavalidator", version=TOOLVERSION, src="https://github.com/proycon/foliatools", metadata={"valid": "yes"}) )
            xml = document.xmlstring(form=folia.Form.EXPLICIT if kwargs.get('explicit') else folia.Form.NORMAL)
            if kwargs.get('output'):
                if folia.checkversion(document.version, "2.0.0") < 0 and not kwargs.get('keepversion') and not kwargs.get('autodeclare'):
                    print("WARNING: Document is valid but can't output older FoLiA (< v2) document unless you specify either --keepversion or --autodeclare to attempt to upgrade. However, if you really want to upgrade the document, use the 'foliaupgrade' tool instead." , file=sys.stderr)
                    return False
                else:
                    print(xml)
        except Exception as e:
            print("SERIALISATION ERROR (stage 3/3): Document validated succesfully but failed to serialise! (" + filename + "). This may be indicative of a problem in the underlying library, please submit an issue on https://github.com/proycon/foliapy with the output of this error.",file=sys.stderr)
            print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
            print("-- Full traceback follows -->",file=sys.stderr)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_exception(ex_type, ex, tb)
            return False
    if kwargs.get('autodeclare'):
        print("Validated successfully **after** applying auto-declarations: " +  filename + " (this is not a guarantee that the original file is valid but indicates it can be automatically made valid!)", file=sys.stderr)
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
    parser.add_argument('-q','--quick',help="Quicker validation; skips RelaxNG validation and serialisation checks", action='store_true', default=False)
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml")
    parser.add_argument('-W','--nowarn',help="Suppress warnings", action='store_true', default=False)
    parser.add_argument('-i','--ignore',help="Always report a successful exit code, even in case of validation errors", action='store_true', default=False)
    parser.add_argument('-t','--stricttextvalidation',help="Treat text validation errors strictly for FoLiA < v1.5,  it always enabled for for FoLiA v1.5+ regardless of this parameter", action='store_true', default=False)
    parser.add_argument('-o','--output',help="Output document to stdout. This output contains added proof of validation to the provenance chain (not cryptographically secure though!)", action='store_true', default=False)
    parser.add_argument('-k','--keepversion',help="Attempt to keep an older FoLiA version (not always guaranteed to work)", action='store_true', default=False)
    parser.add_argument('-D','--debug',type=int,help="Debug level", action='store',default=0)
    parser.add_argument('-b','--traceback',help="Provide a full traceback on validation errors", action='store_true', default=False)
    parser.add_argument('-x','--explicit',help="Serialise to explicit form, this generates more verbose XML and simplified the job for parsers as implicit information is made explicit", action='store_true', default=False)
    parser.add_argument('--fixunassignedprocessor',help="Fixes invalid FoLiA that does not explicitly assign a processor to an annotation when multiple processors are possible (and there is therefore no default). The last processor will be used in this case.", action='store_true', default=False)
    return parser

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    commandparser(parser)
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to validate')
    args = parser.parse_args()

    schema  = lxml.etree.RelaxNG(folia.relaxng())

    if args.explicit:
        args.output = True

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

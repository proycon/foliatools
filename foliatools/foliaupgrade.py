#!/usr/bin/env python3

import sys
import os.path
import argparse
import glob
import shutil
import folia.main as folia
from foliatools import VERSION
from foliatools.foliavalidator import validate

def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-V', '--version',help="Output version information", action='store_true')
    parser.add_argument('-n', '--dryrun',help="Dry run, do not write files", action='store_true', default=False)
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml",required=False)
    parser.add_argument('files', nargs='+', help='Input files')
    args = parser.parse_args()

    if args.version:
        print("FoLiA " + folia.FOLIAVERSION + ", library version " + folia.LIBVERSION,file=sys.stderr)
        sys.exit(0)

    success = process(*args.files, **args.__dict__)
    sys.exit(0 if success else 1)

def annotators2processors(doc, mainprocessor):
    """Convert FoLiA v1 style annotators to v2 style processors (limited)"""
    for element in doc.items():
        if isinstance(element, folia.AbstractElement):
            if element.annotator:
                if element.annotatortype == folia.ProcessorType.MANUAL:
                    annotatortype = folia.ProcessorType.MANUAL
                else:
                    annotatortype = folia.ProcessorType.AUTO
                foundprocessor = None
                for processor in doc.getprocessors(element.ANNOTATIONTYPE, element.set):
                    if element.annotator == processor.name and annotatortype == processor.type:
                        foundprocessor = processor
                if foundprocessor:
                    element.processor = foundprocessor
                else:
                    #Create a new processor
                    newprocessor = folia.Processor(element.annotator, type=annotatortype)
                    mainprocessor.append(newprocessor)
                    element.setprocessor(newprocessor)
                #delete the old style annotator
                element.annotator = None
                element.annotatortype = None


def process(*files, **kwargs):
    success = False
    for file in files:
        if os.path.isdir(file):
            r = process(list(glob.glob(os.path.join(file, "*." + kwargs['extension'] )) ), **kwargs)
            if r != 0:
                success = False
        elif os.path.isfile(file):
            mainprocessor = folia.Processor.create(name="foliaupgrade", version=VERSION)
            doc = validate(file,schema=None, stricttextvalidation=True,autodeclare=True,output=False, warn=False,processor=mainprocessor,traceback=True,**kwargs)
            if doc is not False:
                print("Upgrading " + doc.filename,file=sys.stderr)
                doc.version = folia.FOLIAVERSION #upgrading involves more than just bumping the number, but that is handled implicitly already by the library when reading the document
                annotators2processors(doc, mainprocessor)
                doc.save(doc.filename + ".upgraded")
                if not validate(file + ".upgraded",schema=None,stricttextvalidation=True,autodeclare=False,traceback=True,**kwargs):
                    print("Upgrade failed",file=sys.stderr)
                    success = False
                else:
                    print("Upgrade OK",file=sys.stderr)
                    if kwargs.get('dryrun'):
                        os.unlink(doc.filename+".upgraded")
                        print(doc.xmlstring())
                    else:
                        shutil.move(doc.filename + ".upgraded", file)
            else:
                success  = False
    return success

if __name__ == "__main__":
    main()

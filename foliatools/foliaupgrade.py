#!/usr/bin/env python3

import sys
import os.path
import argparse
import glob
import shutil
import folia.main as folia
from socket import getfqdn
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

def convert_set(annotationtype, annotationset):
    if annotationset == "undefined":
        if annotationtype == folia.AnnotationType.TEXT:
            return folia.DEFAULT_TEXT_SET
        elif annotationtype == folia.AnnotationType.PHON:
            return folia.DEFAULT_PHON_SET
        else:
            return None
    else:
        return annotationset

def convert_undefined_sets(doc):
    exempt = set()
    for element in doc.items():
        if isinstance(element, folia.AbstractElement):
            if element.set == "undefined" and element.cls:
                exempt.add(element.ANNOTATIONTYPE)
    for element in doc.items():
        if isinstance(element, folia.AbstractElement):
            if element.set == "undefined" and element.ANNOTATIONTYPE not in exempt:
                element.set = None
    doc.annotations = [ (annotationtype, convert_set(annotationtype, annotationset) ) for annotationtype, annotationset in doc.annotations ]


def annotators2processors(doc, mainprocessor):
    """Convert FoLiA v1 style annotators to v2 style processors (limited)"""
    for element in doc.items():
        if isinstance(element, folia.AbstractElement):
            if element.annotator is not None:
                element.annotator2processor(element.annotator, element.annotatortype, parentprocessor=mainprocessor) #the library does the bulk of the work for us
            elif element.annotatortype is not None:
                element.annotator2processor("unspecified", element.annotatortype, parentprocessor=mainprocessor) #the library does the bulk of the work for us
    doc.annotationdefaults = {} #not needed anymore

def upgrade(doc, upgradeprocessor):
    assert doc.autodeclare

    if not doc.provenance or (len(doc.provenance) == 1 and doc.provenance.processors[0] == upgradeprocessor):
        #add a datasource processor as the first one
        doc.provenance.insert(0, folia.Processor(doc.id + ".pre-upgrade", folia_version=doc.version, type=folia.ProcessorType.DATASOURCE, host=getfqdn(), src="file://" + doc.filename, format="text/folia+xml"))

    #bump the version number
    doc.version = folia.FOLIAVERSION
    #convert old style annotators to new style processors
    annotators2processors(doc, upgradeprocessor)
    #convert undefined sets
    convert_undefined_sets(doc)


def process(*files, **kwargs):
    success = False
    for file in files:
        if os.path.isdir(file):
            r = process(list(glob.glob(os.path.join(file, "*." + kwargs['extension'] )) ), **kwargs)
            if r != 0:
                success = False
        elif os.path.isfile(file):
            mainprocessor = folia.Processor.create(name="foliaupgrade", version=VERSION, src="https://github.com/proycon/foliatools")
            doc = validate(file,schema=None, stricttextvalidation=True,autodeclare=True,output=False, warn=False,processor=mainprocessor,traceback=True,**kwargs)
            if doc is not False:
                print("Upgrading " + doc.filename,file=sys.stderr)
                upgrade(doc, mainprocessor)
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

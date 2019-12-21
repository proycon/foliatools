#!/usr/bin/env python3

"""Automatically upgrade older FoLiA documents to the latest version. Also has the ability to apply certain fixes."""

import sys
import os.path
import argparse
import glob
import shutil
import folia.main as folia
from socket import getfqdn
from foliatools import VERSION as TOOLVERSION
from foliatools.foliavalidator import validate


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('-n', '--dryrun',help="Dry run, do not write files", action='store_true', default=False)
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml",required=False)
    parser.add_argument('--fixunassignedprocessor',help="Fixes invalid FoLiA that does not explicitly assign a processor to an annotation when multiple processors are possible (and there is therefore no default). The last processor will be used in this case.", action='store_true', default=False)
    parser.add_argument('files', nargs='+', help='Input files')
    args = parser.parse_args()

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

def convert_undefined_sets(doc, elements = None):
    if elements is None: elements = doc.elements()
    exempt = set()
    for element in elements:
        if element.set == "undefined" and element.cls:
            exempt.add(element.ANNOTATIONTYPE)
    for element in elements:
        if element.set == "undefined" and element.ANNOTATIONTYPE not in exempt:
            element.set = None
    doc.annotations = [ (annotationtype, convert_set(annotationtype, annotationset) ) for annotationtype, annotationset in doc.annotations ]


def annotators2processors(doc, mainprocessor, elements=None):
    """Convert FoLiA v1 style annotators to v2 style processors (limited)"""
    if elements is None: elements = doc.elements()
    for element in doc.elements():
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
    elements = doc.elements()
    #convert old style annotators to new style processors
    annotators2processors(doc, upgradeprocessor, elements)
    #convert undefined sets
    convert_undefined_sets(doc, elements)


def process(*files, **kwargs):
    success = False
    for file in files:
        if os.path.isdir(file):
            files = list(glob.glob(os.path.join(file, "*." + kwargs['extension'] )) )
            r = process(files, **kwargs)
            if files and r:
                success = True
        elif os.path.isfile(file):
            mainprocessor = folia.Processor.create(name="foliaupgrade", version=TOOLVERSION, src="https://github.com/proycon/foliatools")
            doc = validate(file,schema=None, stricttextvalidation=True,autodeclare=True,output=False, warn=False,processor=mainprocessor,traceback=True,**kwargs)
            if doc is not False:
                print("Upgrading " + doc.filename,file=sys.stderr)
                upgrade(doc, mainprocessor)
                doc.save(doc.filename + ".upgraded")
                if not validate(file + ".upgraded",schema=None,stricttextvalidation=True,autodeclare=False,traceback=True,**kwargs):
                    print("Upgrade failed",file=sys.stderr)
                    success = False
                else:
                    success = True
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

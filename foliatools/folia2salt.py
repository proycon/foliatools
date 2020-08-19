#!/usr/bin/env python3

"""FoLiA to Salt XML conversion. Can in turn be used by Pepper for further conversion to other formats."""

import sys
import os
import argparse
import glob
from lxml.builder import ElementMaker
from foliatools import VERSION as TOOLVERSION
import folia.main as folia

E = ElementMaker(nsmap={"sDocumentStructure":"sDocumentStucture", "xmi":"http://www.omg.org/XMI", "saltCore":"saltCore" })


def processdir(d, **kwargs):
    success = False
    print("Searching in  " + d,file=sys.stderr)
    extension = kwargs.get('extension','xml').strip('.')
    for f in glob.glob(os.path.join(d ,'*')):
        r = True
        if f[-len(extension) - 1:] == '.' + extension:
            r = convert(f, **kwargs)
        elif kwargs.get('recurse') and os.path.isdir(f):
            r = processdir(f,**kwargs)
        if not r: success = False
    return success

def convert(f, **kwargs):
    success = False
    doc = folia.Document(file=f)
    if not doc.declared(folia.AnnotationType.TOKEN):
        raise Exception("Only tokenized documents can be handled at the moment")

    tokens = []
    textrelations = []

    nodes_seqnr = 0 #first node will hold TextualDS

    map_id_to_nodenr = {}

    text = ""
    for word in doc.select(folia.Word):
        if not word.id:
            raise Exception("Only documents in which all words have IDs can be converted. Consider preprocessing with foliaid first.")

        textstart = len(text)
        text += word.text()
        textend = len(text)

        nodes_seqnr += 1
        map_id_to_nodenr[word.id] = nodes_seqnr
        tokens.append(
            E.nodes({
                    "xsi:type": "sDocumentStructure:SToken",
                    },
                    E.labels({
                        "xsi:type": "saltCore:SElementId",
                        "namespace": "salt",
                        "name": "id",
                        "value": "T::salt:" + kwargs.corpusprefix + "/" + doc.id + '#' + word.id
                    }),
                    E.labels({
                        "xsi:type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SNAME",
                        "value": "T::" + word.id
                    }),
                    *convert_inline_annotations(word)
            )
        )

        textrelations.append(
            E.edges({
                    "xsi:type": "sDocumentStructure:STextualRelation",
                    "source": f"//@nodes.{nodes_seqnr}",
                    "target": "//@nodes.0"
                    },
                    E.labels({
                        "xsi:type": "saltCore:SElementId",
                        "namespace": "salt",
                        "name": "id",
                        "value": "T::salt:" + kwargs.corpusprefix + "/" + doc.id + '#sTextRel' + str(len(textrelations)+1)
                    }),
                    E.labels({
                        "xsi:type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SNAME",
                        "value": "T::sTextRel" + str(len(textrelations)+1)
                    }),
                    E.labels({
                        "xsi:type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SSTART",
                        "value": "N::{textstart}"
                    }),
                    E.labels({
                        "xsi:type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SEND",
                        "value": "N::{textend}"
                    })
            )
        )

        if word.space:
            text += " "



    saltdoc = E.element( #sDocumentGraph
        {"xmi:version":"2.0"},
        E.labels({ # document ID
            "xsi:type": "saltCore:SElementId",
            "namespace": "salt",
            "name": "id",
            "value": "T::salt:" + kwargs.corpusprefix + "/" + doc.id
        }),
        E.nodes({
                    "xsi:type": "sDocumentStructure:STextualDS",
                },
                E.labels({
                    "xsi:type": "saltCore:SFeature",
                    "namespace": "saltCommon",
                    "name": "SDATA",
                    "value": "T::" + text, #this can be huge!
                }),
                E.labels({
                    "xsi:type": "saltCore:SElementId",
                    "namespace": "salt",
                    "name": "id",
                    "value": "T::salt:" + kwargs.corpusprefix + "/" + doc.id + '#sTextualDS'
                }),
                E.labels({
                    "xsi:type": "saltCore:SFeature",
                    "namespace": "salt",
                    "name": "SNAME",
                    "value": "T::sTextualDS"
                }),
        ),
        *tokens,
        *textrelations,
        name="sDocumentGraph", ns="sDocumentStructure")
    return saltdoc

def convert_inline_annotations(word, **kwargs):
    #TODO: to be implemented still
    return []



def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--recurse','-r',help="recurse into subdirectories", action='store_true', required=False)
    parser.add_argument('--extension','-e',type=str, help="extension", action='store', default="xml",required=False)
    parser.add_argument('--corpusprefix',type=str, help="Corpus prefix for salt", action='store', default="/corpus",required=False)
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to convert')
    args = parser.parse_args()

    if args.files:
        success = True
        skipnext = False
        for file in args.files:
            r = False
            if os.path.isdir(file):
                r = processdir(file, **args.__dict__)
            elif os.path.isfile(file):
                saltdoc = convert(file, **args.__dict__)
            else:
                print("ERROR: File or directory not found: " + file,file=sys.stderr)
                sys.exit(3)
            if not r: success= False
        if not success:
            sys.exit(1)
    else:
        print("ERROR: No files specified. Add --help for usage details.",file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
Splits a FoLiA document into multiple separate FoLiA documents based on user-specified selection criteria.
"""

import sys
import os
import argparse
from copy import deepcopy
from foliatools import VERSION as TOOLVERSION
import folia.main as folia
import folia.fql as fql

def split(doc, expression, batchsize=1, copymetadata=False, require_submetadata=False,  suffix_template="_{:04d}", alter_ids=False, external=False, callback=None):
    query = fql.Query("SELECT " + expression)
    childdoc = None
    prevmatch = None
    docnr = 0
    for match in query(doc):
        if require_submetadata and match.metadata is None:
            continue
        if prevmatch and prevmatch in match.ancestors():
            #prevent recursion within elements that are already split into documents
            continue
        if callback and not callback(match):
            continue
        if not childdoc:
            docnr += 1
            id_suffix = suffix_template.format(docnr)
            childdoc = folia.Document(id=doc.id + id_suffix )
            if copymetadata:
                childdoc.metadata = deepcopy(doc.metadata)
            childdoc.annotations = deepcopy(doc.annotations)
            childdoc.annotators = deepcopy(doc.annotators)
            childdoc.annotator2processor_map = deepcopy(doc.annotator2processor_map)
            childdoc.groupannotations = deepcopy(doc.groupannotations)
            childdoc.provenance = deepcopy(doc.provenance)
            childdoc.provenance.append(folia.Processor.create(name="foliasplit", version=TOOLVERSION))
            childdoc.alias_set = deepcopy(doc.alias_set)
            childdoc.set_alias = deepcopy(doc.set_alias)
            childdoc.textclasses = deepcopy(doc.textclasses)
            if match.metadata:
                #copy submetadata to new document's metadata
                try:
                    submetadata = doc.submetadata[match.metadata]
                except KeyError:
                    print("WARNING: Submetadata not found: " + match.metadata,file=sys.stderr)
                    submetadata = None
                if submetadata:
                    for key, value in submetadata.items():
                        childdoc.metadata[key] = value
            #add main body element (text or speech)
            body = childdoc.append(doc.data[0].__class__(childdoc, id=doc.id + id_suffix + "."  + doc.data[0].XMLTAG))
        matchcopy = match.copy(childdoc, id_suffix if alter_ids else "")
        matchcopy.metadata = None
        body.append(matchcopy)
        if len(body.data) == batchsize:
            yield childdoc
            childdoc = None
            body = None
        prevmatch = match
    if childdoc:
        yield childdoc

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--copymetadata','-m',help="Copy all metadata from the parent document to the children", action='store_true', required=False)
    parser.add_argument('--batchsize','-b',type=int, help="Batch size: create documents with this many matches", action='store', required=False, default=1)
    parser.add_argument('--alterids','-i',help="Alter the IDs of all split elements by appending a suffix", action='store_true', required=False)
    parser.add_argument('--suffixtemplate',help="A template for adding suffixes to IDs, in Python's format syntax", action='store_true', required=False, default="_{:04d}")
    parser.add_argument('--submetadata',help="Only split elements that have associated submetadata (extra parameter as the query can't capture this)", action='store_true', required=False)
    parser.add_argument('--query','-q',type=str, help="Query to select elements to split, this is an FQL SELECT expression without the SELECT statement, it can be as simple as the element type, e.g. s for sentences or more complex like: 'div OF https://your.set WHERE class = \"chapter\"' ", action='store', required=True)
    parser.add_argument('--outputdir','-o',type=str, help="Output directory", action='store', required=False,default=".")
    parser.add_argument("--external","-x",  action='store_true', help="Replace split-off elements with <external> elements in the original input document (this only works if they are directly under the root element)", required=False)
    parser.add_argument("files", nargs="*", help="The FoLiA documents to split")
    args = parser.parse_args()
    for filename in args.files:
        doc = folia.Document(file=filename)
        for i, childdoc in enumerate(split(doc, args.query, args.batchsize, args.copymetadata, args.submetadata, args.suffixtemplate, args.alterids, args.external)):
            print(f"#{i} - " + childdoc.id + ".folia.xml", file=sys.stderr)
            childdoc.save(os.path.join(args.outputdir, childdoc.id) + ".folia.xml")

if __name__ == "__main__":
    main()

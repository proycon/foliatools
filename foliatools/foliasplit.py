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

def split(doc, expression, batchsize=1, copymetadata=False, require_submetadata=False,  suffix_template="_{:04d}", alter_ids=False, external=False, callback=None, deep=False):
    query = fql.Query("SELECT " + expression)
    childdoc = None
    prevmatch = None
    docnr = 0
    substituted = False #ensure we only substitute once per batch (when external is enabled)
    if external:
        proc = doc.provenance.append(folia.Processor.create(name="foliasplit", version=TOOLVERSION))
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
            if deep:
                childdoc.annotations = deepcopy(doc.annotations)
                childdoc.annotators = deepcopy(doc.annotators)
                childdoc.annotator2processor_map = deepcopy(doc.annotator2processor_map)
                childdoc.groupannotations = deepcopy(doc.groupannotations)
                childdoc.alias_set = deepcopy(doc.alias_set)
                childdoc.set_alias = deepcopy(doc.set_alias)
                childdoc.textclasses = deepcopy(doc.textclasses)
            else:
                childdoc.annotations = doc.annotations
                childdoc.annotators = doc.annotators
                childdoc.annotator2processor_map = doc.annotator2processor_map
                childdoc.groupannotations = doc.groupannotations
                childdoc.alias_set = doc.alias_set
                childdoc.set_alias = doc.set_alias
                childdoc.textclasses = doc.textclasses
            childdoc.provenance = deepcopy(doc.provenance)
            if not external:
                childdoc.provenance.append(folia.Processor.create(name="foliasplit", version=TOOLVERSION))
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
            if external:
                if substituted:
                    match.parent.data.remove(match)
                else:
                    i = match.parent.getindex(match)
                    if i == -1:
                        raise Exception("Unable to find child from parent! This shouldn't happen")
                    match.parent.data[i] = folia.External(doc, src=childdoc.id + ".folia.xml", id=childdoc.id, processor=proc)
                    substituted = True
        if deep:
            matchcopy = match.copy(childdoc, id_suffix if alter_ids else "") #deep copy
        else:
            matchcopy = match.move(childdoc, id_suffix if alter_ids else "") #shallow copy
        matchcopy.metadata = None
        body.append(matchcopy)
        if len(body.data) == batchsize:
            yield childdoc
            childdoc = None
            body = None
            substituted = False
        prevmatch = match
    if childdoc:
        yield childdoc



def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--copymetadata','-m',help="Copy all metadata from the parent document to the children", action='store_true', required=False)
    parser.add_argument('--batchsize','-b',type=int, help="Batch size: create documents with this many matches", action='store', required=False, default=1)
    parser.add_argument('--alterids','-i',help="Alter the IDs of all split elements by appending a suffix", action='store_true', required=False)
    parser.add_argument('--deep',help="Make a deep copy (slower)", action='store_true', required=False)
    parser.add_argument('--suffixtemplate',help="A template for adding suffixes to IDs, in Python's format syntax", action='store_true', required=False, default="_{:04d}")
    parser.add_argument('--submetadata',help="Only split elements that have associated submetadata (extra parameter as the query can't capture this)", action='store_true', required=False)
    parser.add_argument('--query','-q',type=str, help="Query to select elements to split, this is an FQL SELECT expression without the SELECT statement, it can be as simple as the element type, e.g. s for sentences or more complex like: 'div OF https://your.set WHERE class = \"chapter\"' ", action='store', required=True)
    parser.add_argument('--outputdir','-o',type=str, help="Output directory", action='store', required=False,default=".")
    parser.add_argument("--external","-x",  action='store_true', help="Replace split-off elements with <external> elements in the original input document. Output the input document (this may overwrite the input if you it's in your immediate working dir and you didn't specify a custom --outputdir!)" , required=False)
    parser.add_argument("files", nargs="*", help="The FoLiA documents to split")
    args = parser.parse_args()

    if args.external and args.batchsize > 1:
        print("WARNING: You are using the external mechanism with a batchsize greater than 1, this may produce wrongly ordered output depending on your query and your input. Please inspect your parent document to make sure the results are sensible.",file=sys.stderr)

    if len(args.files) < 1:
        print("No files specified. Run with --help for usage info.", file=sys.stderr)

    #parse query prior to reading files just to make sure there are no syntax errors
    fql.Query("SELECT " + args.query)

    for filename in args.files:
        print("Loading " + filename, file=sys.stderr)
        doc = folia.Document(file=filename)
        for i, childdoc in enumerate(split(doc, args.query, args.batchsize, args.copymetadata, args.submetadata, args.suffixtemplate, args.alterids, args.external, None, args.deep)):
            print("#" + str(i+1) + " - " + childdoc.id + ".folia.xml", file=sys.stderr)
            childdoc.save(os.path.join(args.outputdir, childdoc.id) + ".folia.xml")

        if args.external:
            print("Saving parent document - " + os.path.basename(filename), file=sys.stderr)
            doc.save(os.path.join(args.outputdir, os.path.basename(filename)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""FoLiA to STAM conversion"""

import sys
import os
import argparse
import glob
from collections import OrderedDict
from foliatools import VERSION as TOOLVERSION
from typing import Generator, Optional
import folia.main as folia
import stam

#Namespace for STAM annotationset and for RDF, not the same as XML namepace because that one is very old and hard to resolve
FOLIA_NAMESPACE = "https://w3id.org/folia/"


def processdir(d, annotationstore: stam.AnnotationStore, **kwargs):
    print("Searching in  " + d,file=sys.stderr)
    extension = kwargs.get('extension','xml').strip('.')
    for f in glob.glob(os.path.join(d ,'*')):
        if f[-len(extension) - 1:] == '.' + extension:
            convert(f, annotationstore,  **kwargs)
        elif kwargs.get('recurse') and os.path.isdir(f):
            processdir(f, annotationstore, **kwargs)

def convert(f, annotationstore: stam.AnnotationStore,  **kwargs):
    """Convert a FoLiA document to STAM"""
    doc = folia.Document(file=f)
    if not doc.declared(folia.AnnotationType.TOKEN):
        raise Exception("Only tokenized documents can be handled at the moment")

    resource = convert_tokens(doc, annotationstore, **kwargs)
    convert_structure_annotation(doc, annotationstore, resource)
    convert_span_annotation(doc, annotationstore, resource, **kwargs)

    #span_nodes, span_spanningrelations, nodes_seqnr = convert_span_annotations(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
    #syntax_nodes, syntax_dominancerelations, nodes_seqnr = convert_syntax_annotation(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)

    selector = stam.Selector.resourceselector(resource)
    if doc.metadata:
        for key, value in doc.metadata.items():
            annotationstore.annotate(target=selector, data={"key":key,"value":value,"set":"metadata"}) #TODO: make metadata set configurable


def convert_tokens(doc: folia.Document, annotationstore: stam.AnnotationStore, **kwargs) -> stam.TextResource:
    """Convert FoLiA tokens (w) and text content to STAM. Returns a STAM resource"""
    tokens = []

    text = ""
    prevword = None

    for word in doc.words():
        if not word.id:
            raise Exception("Only documents in which all words have IDs can be converted. Consider preprocessing with foliaid first.")

        textstart = len(text)
        try:
            text += word.text()
        except folia.NoSuchText:
            pass
        textend = len(text)

        tokens.append({
            "id": word.id,
            "begin": textstart,
            "end": textend,
            "data": list(convert_type_information(word)) + \
                    list(convert_common_attributes(word)) 
        })

        #associate offsets with the FoLiA element for convenience later
        word._begin = textstart
        word._end = textend

        if text and textstart != textend:
           if word.space or (prevword and word.parent != prevword.parent):
               text += " "

    if not text:
        raise Exception(f"Document {doc.filename} has no text!")

    if kwargs['external_resources']: 
        #write text as standoff document
        filename = os.path.join(kwargs['outputdir'], doc.id + ".txt")
        with open(filename,'w',encoding='utf-8') as f:
            f.write(text)
        #reads it again and associates it with the store:
        resource = annotationstore.add_resource(id=doc.id, filename=filename)
    else:
        resource = annotationstore.add_resource(id=doc.id, text=text)

    for token in tokens:
        word_stam = annotationstore.annotate(id=token["id"], 
                                             target=stam.Selector.textselector(resource, stam.Offset.simple(token["begin"], token["end"])),
                                             data=token["data"])

        word_folia = doc[token["id"]]
        if word_folia:
            convert_inline_annotation(word_folia, word_stam, annotationstore, **kwargs )

    return resource

       #    textrelations.append(
       #        E.edges({
       #            "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:STextualRelation",
       #                "source": f"//@nodes.{nodes_seqnr}",
       #                "target": f"//@nodes.{textnode}"
       #                },
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
       #                    "namespace": "salt",
       #                    "name": "id",
       #                    "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#sTextRel' + str(len(textrelations)+1)
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SNAME",
       #                    "value": "T::sTextRel" + str(len(textrelations)+1)
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SSTART",
       #                    "value": f"N::{textstart}"
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SEND",
       #                    "value": f"N::{textend}"
       #                })
       #        )
       #    )

       #    if word.space or (prevword and word.parent != prevword.parent):
       #        text += " "

       #if phon and phonstart != phonend:
       #    phonrelations.append(
       #        E.edges({
       #            "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:STextRelation",
       #                "source": f"//@nodes.{nodes_seqnr}",
       #                "target": "//@nodes.{phonnode}"
       #                },
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
       #                    "namespace": "salt",
       #                    "name": "id",
       #                    "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#sPhonRel' + str(len(phonrelations)+1)
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SNAME",
       #                    "value": "T::sPhonRel" + str(len(phonrelations)+1)
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SSTART",
       #                    "value": f"N::{phonstart}"
       #                }),
       #                E.labels({
       #                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
       #                    "namespace": "salt",
       #                    "name": "SEND",
       #                    "value": f"N::{phonend}"
       #                })
       #        )
       #    )


       #prevword = word

    #nodes = []
    #if text:
    #    nodes.append( E.nodes({
    #        "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:STextualDS",
    #                        },
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
    #                            "namespace": "saltCommon",
    #                            "name": "SDATA",
    #                            "value": "T::" + text, #this can be huge!
    #                        }),
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
    #                            "namespace": "salt",
    #                            "name": "id",
    #                            "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#TextContent'
    #                        }),
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
    #                            "namespace": "salt",
    #                            "name": "SNAME",
    #                            "value": "T::TextContent"
    #                        }),
    #                ))
    #if phon:
    #    nodes.append(E.nodes({
    #        "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:STextualDS",
    #                        },
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
    #                            "namespace": "saltCommon",
    #                            "name": "SDATA",
    #                            "value": "T::" + phon, #this can be huge!
    #                        }),
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
    #                            "namespace": "salt",
    #                            "name": "id",
    #                            "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#PhonContent'
    #                        }),
    #                        E.labels({
    #                            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
    #                            "namespace": "salt",
    #                            "name": "SNAME",
    #                            "value": "T::PhonContent"
    #                        }),
    #                ))

    


def convert_inline_annotation(word: folia.Word, word_stam: stam.Annotation, annotationstore: stam.AnnotationStore, **kwargs):
    """Convert FoLiA inline annotations to STAM."""


    #create an AnnotationSelector to the token
    if kwargs['inline_annotations_mode'] == "annotationselector":
        selector = stam.Selector.annotationselector(word_stam, stam.Offset.whole())
    elif kwargs['inline_annotations_mode'] == "textselector":
        #select the text directly, just get the selector from the STAM annotation for the token
        selector = word_stam.target()
    else:
        raise Exception("invalid value for --inline-annotations-mode")

    for annotation_folia in word.select(folia.AbstractInlineAnnotation):
        data = list(convert_type_information(annotation_folia)) +  \
               list(convert_common_attributes(annotation_folia)) + \
               list(convert_features(annotation_folia)) 
        if annotation_folia.id:
            annotationstore.annotate(id=annotation_folia.id, target=selector, data=data)
        else:
            annotationstore.annotate(target=selector, data=data)

        #TODO: list(convert_higher_order(annotation_folia))
        


def convert_structure_annotation(doc: folia.Document, annotationstore: stam.AnnotationStore, resource: stam.TextResource):
    """Convert FoLiA structure annotations (sentences, paragraphs, etc) to STAM
    In this conversion the structure annotations directly reference the underlying text, rather than other underlying structural elements like FoLiA does.
    """

    #Create spans and text relations for all structure elements
    for structure in doc.select(folia.AbstractStructureElement):
        if not isinstance(structure, folia.Word): #word are already covered
            firstword =  None
            lastword = None
            for word in structure.select(folia.Word):
                if firstword is None: firstword = word
                lastword = word
            if firstword is None and lastword is None:
                print("WARNING: Unable to convert untokenised structure "  + structure.id, file=sys.stderr)
                continue
            if not hasattr(firstword, "_begin") or firstword._begin is None or  not hasattr(lastword, "_end") and lastword._end is None: #type: ignore
                print("WARNING: Failed to extract offsets for structure"  + structure.id, file=sys.stderr)
                continue
            data =  list(convert_type_information(structure)) + \
                    list(convert_common_attributes(structure)) + \
                    list(convert_features(structure)) 
            annotationstore.annotate(id=structure.id, 
                                     target=stam.Selector.textselector(resource, stam.Offset.simple(firstword._begin, lastword._end)), data=data) #type: ignore

    #TODO: convert_higher_order

def convert_span_annotation(doc: folia.Document, annotationstore: stam.AnnotationStore, resource: stam.TextResource, **kwargs):
    """Convert FoLiA span annotations (sentences, paragraphs, etc) to STAM annotations with a CompositeSelector.
    In this conversion the span annotations may either directly reference the underlying text, 
    or point to the tokens, depending on the setting for span-annotations-mode.
    """

    for span in doc.select(folia.AbstractSpanAnnotation):
        #if not isinstance(span, (folia.AbstractSpanRole, folia.SyntacticUnit)) and  not any((isinstance(x, folia.AbstractSpanRole) for x in span.ACCEPTED_DATA)):

        selectors = []
        if kwargs['span_annotations_mode'] == "annotationselector":
            for w in span.wrefs():
                word_stam = annotationstore.annotation(w.id)
                selectors.append(stam.Selector.annotationselector(word_stam, stam.Offset.whole()))
        elif kwargs['span_annotations_mode'] == "textselector":
            #select the text directly, merge adjacent tokens into one selection
            firstword = None
            prevword = None
            for w in span.wrefs():
                if firstword is None:
                    firstword = w
                if prevword and prevword.next(folia.Word) != w:
                    if not hasattr(firstword, "_begin") or not hasattr(prevword, "_end"): #type: ignore
                        print("WARNING: Failed to extract offsets for span"  + span.id, file=sys.stderr)
                        continue
                    selectors.append(stam.Selector.textselector(resource, stam.Offset.simple(firstword._begin, prevword._end))) #type: ignore
                    firstword = None
                prevword = w
            if firstword and prevword:
                selectors.append(stam.Selector.textselector(resource, stam.Offset.simple(firstword._begin, prevword._end))) #type: ignore
        else:
            raise Exception("invalid value for --span-annotations-mode")

        data =  list(convert_type_information(span)) + \
                list(convert_common_attributes(span)) + \
                list(convert_features(span)) 

        if span.id:
            if len(selectors) == 1:
                annotationstore.annotate(id=span.id, 
                                     target=selectors[0], data=data) #type: ignore
            else:
                annotationstore.annotate(id=span.id, 
                                     target=stam.Selector.compositeselector(*selectors), data=data) #type: ignore
        else:
            #(nested span roles may not carry an independent ID in FoLiA)
            if len(selectors) == 1:
                annotationstore.annotate(target=selectors[0], data=data) #type: ignore
            else:
                annotationstore.annotate(target=stam.Selector.compositeselector(*selectors), data=data) #type: ignore

        #TODO: Build explicit tree structure for nested annotation (syntax) and span roles

#def convert_syntax_annotation(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
#    syntax_nodes = []
#    syntax_relations = []
#    for syntaxlayer in doc.select(folia.SyntaxLayer):
#        for su in syntaxlayer.select(folia.SyntacticUnit, recursive=False):
#            nodes, relations, nodes_seqnr = convert_nested_span(su, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
#            syntax_nodes += nodes
#            syntax_relations += relations
#    return (syntax_nodes, syntax_relations, nodes_seqnr)
# 
#def convert_nested_span(span, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
#    nested_nodes = []
#    nested_relations = []
#    #process children first
#    children_nodenr = []
#    for child in span.select( (span.__class__, folia.Word), recursive=False):
#        if child.__class__ is span.__class__:
#            nodes, relations, nodes_seqnr = convert_nested_span(child, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
#            nested_nodes += nodes
#            nested_relations += relations
#            children_nodenr.append(child.nodes_seqnr)
#        else:
#            children_nodenr.append(child.nodes_seqnr)
# 
#    layer, namespace = init_layer(layers, span)
#    span.nodes_seqnr = nodes_seqnr #we will need this to get the node number back from the parent elements
#    layer['nodes'].append(nodes_seqnr)
# 
#    nested_nodes.append(
#            E.nodes({
#                "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SStructure", #salt calls nested hierarchies 'structure', not to be confused with what FoLiA calls structure (document structure)
#                },
#                *convert_identifier(span, **kwargs),
#                *convert_type_information(span, **kwargs),
#                *convert_common_attributes(span, namespace, **kwargs),
#                *convert_features(span, namespace, **kwargs),
#                *convert_higher_order(span, namespace, **kwargs),
#            )
#    )
# 
#    for nodenr in children_nodenr:
#        nested_relations.append(
#             E.edges({
#                 "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SDominanceRelation",
#                     "source": f"//@nodes.{nodes_seqnr}", #the span
#                     "target": f"//@nodes.{nodenr}", #the subspan or token
#                 },
#                 E.labels({
#                     "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
#                    "namespace": "salt",
#                    "name": "id",
#                    "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + span.doc.id + f"#sDomRel{nodes_seqnr}-{nodenr}"
#                }),
#                E.labels({
#                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
#                    "namespace": "salt",
#                    "name": "SNAME",
#                    "value": f"T::sDomRel{nodes_seqnr}-{nodenr}"
#                })
#            )
#        )
#    nodes_seqnr += 1
#
#    return (nested_nodes, nested_relations, nodes_seqnr)


def convert_type_information(annotation: folia.AbstractElement) -> Generator[dict,None,None]:
     if annotation.XMLTAG:
        yield { "set":FOLIA_NAMESPACE,
                "id": f"elementtype/{annotation.XMLTAG}",
                "key": "elementtype",
                "value": annotation.XMLTAG}
     if annotation.ANNOTATIONTYPE:
        value = folia.annotationtype2str(annotation.ANNOTATIONTYPE)
        if value:
            value = value.lower()
            yield {"set": FOLIA_NAMESPACE,
                   "id":f"annotationtype/{value}",
                    "key":"annotationtype",
                    "value":value}

def convert_common_attributes(annotation: folia.AbstractElement) -> Generator[dict,None,None]:
    """Convert common FoLiA attributes"""

    # Note: ID is handled separately (it's a common attribute in FoLiA but does not translate to AnnotationData in STAM)

    if annotation.cls is not None and annotation.set is not None:
        yield { "set":annotation.set,
             "key":"class",
             "value":annotation.cls}


    if annotation.confidence is not None:
        yield {"set":FOLIA_NAMESPACE,
            "id":f"confidence/{annotation.confidence}",
            "key":"confidence",
            "value":annotation.confidence}

    if annotation.n is not None:
        yield {"set":FOLIA_NAMESPACE,
            "key":"n",
            "value":annotation.n}

    if annotation.href is not None:
        yield { "set":FOLIA_NAMESPACE,
            "key":"href",
            "value":annotation.href}

    if annotation.datetime is not None:
        value = annotation.datetime.strftime("%Y-%m-%dT%H:%M:%S")
        yield { "set":FOLIA_NAMESPACE,
            "id":f"datetime/{value}",
            "key":"datetime",
            "value":value} #MAYBE TODO: convert to STAM's internal datetime type?

    if annotation.processor:
        yield { "set":FOLIA_NAMESPACE,
            "key":"processor/id",
            "value":annotation.processor.id}
        yield { "set":FOLIA_NAMESPACE,
            "key":"processor/name",
            "value":annotation.processor.name}
        yield { "set":FOLIA_NAMESPACE,
            "id":f"processor/type/{annotation.processor.type}",
            "key":"processor/type",
            "value":annotation.processor.type}

def convert_features(annotation: folia.AbstractElement):
    """Convert FoLiA features to STAM AnnotationData"""
    for feature in annotation.select(folia.Feature, recursive=False):
        yield { "set":annotation.set,
            "key":feature.subset,
            "value":feature.cls}

#def convert_higher_order(annotation, namespace, **kwargs):
#   """Convert certain FoLiA higher-order features to SAnnotation labels (on salt nodes)"""
#   for seqnr, description in enumerate(annotation.select(folia.Description, recursive=False)):
#       yield E.labels({
#           "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SMetaAnnotation",
#                   "namespace": namespace,
#                   "name": "description/" + str(seqnr + 1),
#                   "value": "T::" + description.value
#               })
#
#   for seqnr, comment in enumerate(annotation.select(folia.Comment, recursive=False)):
#       yield E.labels({
#           "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SMetaAnnotation",
#                   "namespace": namespace,
#                   "name": "comment/" + str(seqnr + 1),
#                   "value": "T::" + comment.value
#               })
#


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--recurse','-r',help="recurse into subdirectories", action='store_true', required=False)
    parser.add_argument('--extension','-e',type=str, help="Input extension", action='store', default="xml",required=False)
    parser.add_argument('--id', type=str, help="Identifier for the STAM Annotation Store", action='store', required=True)
    parser.add_argument('--outputdir','-o',type=str, help="Output directory", action='store', default=".", required=False)
    parser.add_argument('--inline-annotations-mode',type=str, help="What STAM selector to use to translate FoLiA's inline annotations? Can be set to AnnotationSelector (reference the tokens) or TextSelector (directly reference the text)", action='store', default="TextSelector", required=False)
    parser.add_argument('--span-annotations-mode',type=str, help="What STAM selector to use to translate FoLiA's span annotations? Can be set to AnnotationSelector (reference the tokens) or TextSelector (directly reference the text)", action='store', default="TextSelector", required=False)
    parser.add_argument('--external-resources',"-X",help="Serialize text to external/stand-off text files rather than including them in the JSON", action='store_true')
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to convert. All will be added to a single STAM annotation store.')
    args = parser.parse_args()

    os.makedirs(os.path.realpath(args.outputdir), exist_ok=True)
    
    args.__dict__['inline_annotations_mode'] = args.__dict__['inline_annotations_mode'].lower()
    assert args.__dict__['inline_annotations_mode'] in ("annotationselector","textselector")
    args.__dict__['span_annotations_mode'] = args.__dict__['span_annotations_mode'].lower()
    assert args.__dict__['span_annotations_mode'] in ("annotationselector","textselector")

    annotationstore = stam.AnnotationStore(id=args.id)
    filename = os.path.join(args.outputdir, args.id + ".store.stam.json")
    annotationstore.set_filename(filename)

    if args.files:
        for file in args.files:
            if os.path.isdir(file):
                processdir(file, annotationstore, **args.__dict__)
            elif os.path.isfile(file):
                convert(file, annotationstore, **args.__dict__)
            else:
                print("ERROR: File or directory not found: " + file,file=sys.stderr)
                sys.exit(3)
    else:
        print("ERROR: No files specified. Add --help for usage details.",file=sys.stderr)
        sys.exit(2)

    annotationstore.save()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""FoLiA to STAM conversion"""

import sys
import os
import argparse
import glob
from collections import OrderedDict
from foliatools import VERSION as TOOLVERSION
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

    layers = OrderedDict()

    resource = convert_tokens(doc, annotationstore, **kwargs)


    structure_nodes, structure_spanningrelations, nodes_seqnr = convert_structure_annotations(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
    span_nodes, span_spanningrelations, nodes_seqnr = convert_span_annotations(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
    syntax_nodes, syntax_dominancerelations, nodes_seqnr = convert_syntax_annotation(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)

    nodes += structure_nodes + span_nodes + syntax_nodes
    edges = textrelations + structure_spanningrelations + span_spanningrelations + syntax_dominancerelations

    layers = list(build_layers(layers, nodes, edges)) #this modifies the nodes and edges as well

    #Create the document (sDocumentGraph)
    saltdoc = getattr(E,"{sDocumentStructure}SDocumentGraph")(
        {"{http://www.omg.org/XMI}version":"2.0"},
        E.labels({ # document ID
            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
            "namespace": "salt",
            "name": "id",
            "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id
        }),
        *nodes,
        *edges,
        *layers)


    metadata = []
    if doc.metadata:
        for key, value in doc.metadata.items():
            metadata.append( E.labels({
                "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SMetaAnnotation",
                "namespace": "FoLiA::meta",
                "name": key,
                "value": "T::" + str(value)
            }) )



def convert_tokens(doc: folia.Document, annotationstore: stam.AnnotationStore, **kwargs) -> stam.TextResource:
    """Convert FoLiA tokens (w) and text content to STAM. Returns a STAM resource"""
    tokens = []
    textrelations = []
    phonrelations = []

    text = ""
    prevword = None

    phon = ""

    #will be initialised on first iteration:
    token_namespace = None


    for word in doc.words():
        if not word.id:
            raise Exception("Only documents in which all words have IDs can be converted. Consider preprocessing with foliaid first.")
        if token_namespace is None:
            #only needs to be done once
            layer, token_namespace = init_layer(layers, word)

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

        #            *convert_inline_annotations(word, layers, **kwargs)

        if text and textstart != textend:
           if word.space or (prevword and word.parent != prevword.parent):
               text += " "


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

    if not text:
        raise Exception(f"Document {doc.filename} has no text!")

    resource = annotationstore.add_resource(id=doc.id, text=text)

    for token in tokens:
        annotationstore.annotate(id=token["id"], 
                                 target=stam.Selector.text(resource, stam.Offset.simple(token["begin"], token["end"])),
                                 data=token["data"])
    return resource
    


def convert_inline_annotations(word: folia.Word, word_stam: stam.Annotation, resource: stam.TextResource, annotationstore: stam.AnnotationStore, **kwargs):
    """Convert FoLiA inline annotations to STAM."""


    #create an AnnotationSelector to the token
    if kwargs['inline-annotations-mode'] == "AnnotationSelector":
        selector = stam.Selector.annotation(word_stam, stam.Offset.whole())
    elif kwargs['inline-annotations-mode'] == "AnnotationSelector":
        selector = stam.Selector.text(resource, word_stam.target())

    for annotation in word.select(folia.AbstractInlineAnnotation):


            layer, namespace = init_layer(layers, annotation)
            if word.nodes_seqnr is not None:
                layer['nodes'].append(word.nodes_seqnr)

            for x in convert_common_attributes(annotation, namespace, **kwargs):
                yield x

            for x in convert_features(annotation, namespace, **kwargs):
                yield x

            for x in convert_higher_order(annotation, namespace, **kwargs):
                yield x

def convert_structure_annotations(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
    """Convert FoLiA structure annotations (sentences, paragraphs, etc) to salt SSpan nodes and SSpaningRelation edges.
    In this conversion the structure annotations directly reference the underlying tokens, rather than other underlying structural elements like FoLiA does.
    """

    structure_nodes = []
    structure_spanningrelations = []
    #Create spans and text relations for all structure elements
    for structure in doc.select(folia.AbstractStructureElement):
        if not isinstance(structure, folia.Word): #word are already covered
            span_nodes = [ map_id_to_nodenr[w.id] for w in structure.words() ]
            if span_nodes:
                layer, namespace = init_layer(layers, structure)
                structure.nodes_seqnr = nodes_seqnr #associate it with the folia temporarily for a quick lookup later
                layer['nodes'].append(nodes_seqnr)
                structure_nodes.append(
                        E.nodes({
                            "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SSpan",
                            },
                            E.labels({ #we follow the example of the TCF->Salt converter here where it is used for sentences, a bit of weird entry, hopefully they knew what they were doing and this triggers some special behaviour for some of the converters? I just made it a bit more generic so it works for all structure types.
                                      "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SAnnotation",
                                "name": folia.annotationtype2str(structure.ANNOTATIONTYPE).lower(),
                                "value": "T::" + folia.annotationtype2str(structure.ANNOTATIONTYPE).lower()
                            }),
                            *convert_identifier(structure, **kwargs),
                            *convert_type_information(structure, **kwargs),
                            *convert_common_attributes(structure, namespace, **kwargs),
                            *convert_features(structure, namespace, **kwargs),
                            *convert_higher_order(structure, namespace, **kwargs),
                        )
                )

                for nodenr in span_nodes:
                    structure_spanningrelations.append(
                         E.edges({
                             "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SSpanningRelation",
                                 "source": f"//@nodes.{nodes_seqnr}", #the structure
                                 "target": f"//@nodes.{nodenr}", #the token in the span
                             },
                             E.labels({
                                 "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
                                "namespace": "salt",
                                "name": "id",
                                "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#sStructureSpanRel' + str(len(structure_spanningrelations)+1)
                            }),
                            E.labels({
                                "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
                                "namespace": "salt",
                                "name": "SNAME",
                                "value": "T::sStructureSpanRel" + str(len(structure_spanningrelations)+1)
                            }),
                        )
                    )
                nodes_seqnr += 1
    return (structure_nodes, structure_spanningrelations, nodes_seqnr)

def convert_span_annotations(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
    """Convert FoLiA span annotations (sentences, paragraphs, etc) to salt SSpan nodes and SSpaningRelation edges.
    In this conversion the span annotations directly reference the underlying tokens, rather than other underlying structural elements like FoLiA does.
    """

    span_nodes = []
    span_spanningrelations = []
    #Create spans and text relations for all span elements:
    #only handles simple span elements that do not take span roles
    for span in doc.select(folia.AbstractSpanAnnotation):
        if not isinstance(span, (folia.AbstractSpanRole, folia.SyntacticUnit)) and  not any((isinstance(x, folia.AbstractSpanRole) for x in span.ACCEPTED_DATA)):
            span_token_nodes = [ map_id_to_nodenr[w.id] for w in span.wrefs() ]
            if span_token_nodes:
                layer, namespace = init_layer(layers, span)
                layer['nodes'].append(nodes_seqnr)

                span_nodes.append(
                        E.nodes({
                            "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SSpan",
                            },
                            *convert_identifier(span, **kwargs),
                            *convert_type_information(span, **kwargs),
                            *convert_common_attributes(span, namespace, **kwargs),
                            *convert_features(span, namespace, **kwargs),
                            *convert_higher_order(span, namespace, **kwargs),
                        )
                )

                for nodenr in span_token_nodes:
                    span_spanningrelations.append(
                         E.edges({
                             "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SSpanningRelation",
                                 "source": f"//@nodes.{nodes_seqnr}", #the span
                                 "target": f"//@nodes.{nodenr}", #the token in the span
                             },
                             E.labels({
                                 "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
                                "namespace": "salt",
                                "name": "id",
                                "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + doc.id + '#sSpanRel' + str(len(span_spanningrelations)+1)
                            }),
                            E.labels({
                                "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
                                "namespace": "salt",
                                "name": "SNAME",
                                "value": "T::sSpanRel" + str(len(span_spanningrelations)+1)
                            })
                        )
                    )
                nodes_seqnr += 1
    return (span_nodes, span_spanningrelations, nodes_seqnr)

def convert_syntax_annotation(doc, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
    syntax_nodes = []
    syntax_relations = []
    for syntaxlayer in doc.select(folia.SyntaxLayer):
        for su in syntaxlayer.select(folia.SyntacticUnit, recursive=False):
            nodes, relations, nodes_seqnr = convert_nested_span(su, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
            syntax_nodes += nodes
            syntax_relations += relations
    return (syntax_nodes, syntax_relations, nodes_seqnr)

def convert_nested_span(span, layers, map_id_to_nodenr, nodes_seqnr, **kwargs):
    nested_nodes = []
    nested_relations = []
    #process children first
    children_nodenr = []
    for child in span.select( (span.__class__, folia.Word), recursive=False):
        if child.__class__ is span.__class__:
            nodes, relations, nodes_seqnr = convert_nested_span(child, layers, map_id_to_nodenr, nodes_seqnr, **kwargs)
            nested_nodes += nodes
            nested_relations += relations
            children_nodenr.append(child.nodes_seqnr)
        else:
            children_nodenr.append(child.nodes_seqnr)

    layer, namespace = init_layer(layers, span)
    span.nodes_seqnr = nodes_seqnr #we will need this to get the node number back from the parent elements
    layer['nodes'].append(nodes_seqnr)

    nested_nodes.append(
            E.nodes({
                "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SStructure", #salt calls nested hierarchies 'structure', not to be confused with what FoLiA calls structure (document structure)
                },
                *convert_identifier(span, **kwargs),
                *convert_type_information(span, **kwargs),
                *convert_common_attributes(span, namespace, **kwargs),
                *convert_features(span, namespace, **kwargs),
                *convert_higher_order(span, namespace, **kwargs),
            )
    )

    for nodenr in children_nodenr:
        nested_relations.append(
             E.edges({
                 "{http://www.w3.org/2001/XMLSchema-instance}type": "sDocumentStructure:SDominanceRelation",
                     "source": f"//@nodes.{nodes_seqnr}", #the span
                     "target": f"//@nodes.{nodenr}", #the subspan or token
                 },
                 E.labels({
                     "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SElementId",
                    "namespace": "salt",
                    "name": "id",
                    "value": "T::salt:/" + kwargs['corpusprefix'] + "/" + span.doc.id + f"#sDomRel{nodes_seqnr}-{nodenr}"
                }),
                E.labels({
                    "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SFeature",
                    "namespace": "salt",
                    "name": "SNAME",
                    "value": f"T::sDomRel{nodes_seqnr}-{nodenr}"
                })
            )
        )
    nodes_seqnr += 1

    return (nested_nodes, nested_relations, nodes_seqnr)


def convert_type_information(annotation):
     if annotation.XMLTAG:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="elementtype",
                                        value=annotation.XMLTAG)
     if annotation.ANNOTATIONTYPE:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="annotationtype",
                                        value=folia.annotationtype2str(annotation.ANNOTATIONTYPE).lower())]

def convert_common_attributes(annotation):
    """Convert common FoLiA attributes"""

    # Note: ID is handled separately (it's a common attribute in FoLiA but does not translate to AnnotationData in STAM)

    if annotation.cls is not None and annotation.set is not None:
        yield stam.AnnotationDataBuilder(annotationset=annotation.set,
                                         key="class",
                                         value=annotation.cls),


    if annotation.confidence is not None:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="confidence",
                                        value=annotation.confidence)

    if annotation.n is not None:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="n",
                                        value=annotation.n)

    if annotation.href is not None:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="href",
                                        value=annotation.href)

    if annotation.datetime is not None:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="datetime",
                                        value=annotation.datetime.strftime("%Y-%m-%dT%H:%M:%S")) #MAYBE TODO: convert to STAM's internal datetime type?

    if annotation.processor:
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="processor/id",
                                        value=annotation.processor.id)
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="processor/name",
                                        value=annotation.processor.name)
        yield stam.AnnotationDataBuilder(annotationset=FOLIA_NAMESPACE,
                                        key="processor/type",
                                        value=annotation.processor.type)

def convert_features(annotation, namespace, **kwargs):
    """Convert FoLiA features to SAnnotation labels (on salt nodes)"""
    for feature in annotation.select(folia.Feature, recursive=False):
        yield E.labels({
            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SAnnotation",
                    "namespace": namespace,
                    "name": "feature/" + feature.subset,
                    "value": "T::" + feature.cls
                })

def convert_higher_order(annotation, namespace, **kwargs):
    """Convert certain FoLiA higher-order features to SAnnotation labels (on salt nodes)"""
    for seqnr, description in enumerate(annotation.select(folia.Description, recursive=False)):
        yield E.labels({
            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "description/" + str(seqnr + 1),
                    "value": "T::" + description.value
                })

    for seqnr, comment in enumerate(annotation.select(folia.Comment, recursive=False)):
        yield E.labels({
            "{http://www.w3.org/2001/XMLSchema-instance}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "comment/" + str(seqnr + 1),
                    "value": "T::" + comment.value
                })



def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--recurse','-r',help="recurse into subdirectories", action='store_true', required=False)
    parser.add_argument('--extension','-e',type=str, help="Input extension", action='store', default="xml",required=False)
    parser.add_argument('--id', type=str, help="Identifier for the STAM Annotation Store", action='store', required=True)
    parser.add_argument('--outputdir','-o',type=str, help="Output directory", action='store', default=".", required=False)
    parser.add_argument('--inline-annotations-mode',type=str, help="What STAM selector to use to translate FoLiA's inline annotations? Can be set to AnnotationSelector (reference the tokens) or TextSelector (directly reference the text)", action='store', default="TextSelector", required=False)
    parser.add_argument('files', nargs='*', help='Files (and/or directories) to convert. All will be added to a single STAM annotation store.')
    args = parser.parse_args()

    os.makedirs(os.path.join(os.path.realpath(args.outputdir), args.corpusprefix), exist_ok=True)

    assert args.__dict__['inline-annotations-mode'] in ("AnnotationSelector","TextSelector")

    annotationstore = stam.AnnotationStore(id=args.id)

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

if __name__ == "__main__":
    main()

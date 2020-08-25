#!/usr/bin/env python3

"""FoLiA to Salt XML conversion. Can in turn be used by Pepper for further conversion to other formats."""

import sys
import os
import argparse
import glob
import lxml.etree
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
    """Convert a FoLiA document to Salt XML"""
    success = False
    doc = folia.Document(file=f)
    if not doc.declared(folia.AnnotationType.TOKEN):
        raise Exception("Only tokenized documents can be handled at the moment")

    tokens, textrelations, text, map_id_to_nodenr, nodes_seqnr = convert_tokens(doc, **kwargs)
    structure_nodes, structure_spanningrelations, nodes_seqnr = convert_structure_annotations(doc, map_id_to_nodenr, nodes_seqnr, **kwargs)
    span_nodes, span_spanningrelations, nodes_seqnr = convert_span_annotations(doc, map_id_to_nodenr, nodes_seqnr, **kwargs)

    #Create the document (sDocumentGraph)
    saltdoc = E.element( #sDocumentGraph
        {"{http://www.omg.org/XMI}version":"2.0"},
        E.labels({ # document ID
            "{http://www.omg.org/XMI}type": "saltCore:SElementId",
            "namespace": "salt",
            "name": "id",
            "value": "T::salt:" + kwargs['corpusprefix'] + "/" + doc.id
        }),
        E.nodes({
                    "{http://www.omg.org/XMI}type": "sDocumentStructure:STextualDS",
                },
                E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                    "namespace": "saltCommon",
                    "name": "SDATA",
                    "value": "T::" + text, #this can be huge!
                }),
                E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SElementId",
                    "namespace": "salt",
                    "name": "id",
                    "value": "T::salt:" + kwargs['corpusprefix'] + "/" + doc.id + '#sTextualDS'
                }),
                E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                    "namespace": "salt",
                    "name": "SNAME",
                    "value": "T::sTextualDS"
                }),
        ),
        *tokens,
        *structure_nodes,
        *span_nodes,
        *textrelations,
        *structure_spanningrelations,
        *span_spanningrelations,
        name="sDocumentGraph", ns="sDocumentStructure")

    outputfile = os.path.basename(doc.filename).replace(".folia.xml","").replace(".xml","") + ".salt"
    xml = lxml.etree.tostring(saltdoc, xml_declaration=True, pretty_print=True, encoding='utf-8')
    with open(outputfile,'wb') as f:
        f.write(xml)
    print(f"Wrote {outputfile}",file=sys.stderr)
    return saltdoc

def convert_tokens(doc, **kwargs):
    """Convert FoLiA tokens (w) to salt nodes. This function also extracts the text layer and links to it."""
    tokens = []
    textrelations = []

    nodes_seqnr = 0 #first node will hold TextualDS

    map_id_to_nodenr = {}

    text = ""
    prevword = None
    token_namespace = None
    for word in doc.words():
        if not word.id:
            raise Exception("Only documents in which all words have IDs can be converted. Consider preprocessing with foliaid first.")
        if token_namespace is None:
            #only needs to be done once
            token_namespace = "FoLiA::w::" + (word.set if word.set else "")

        textstart = len(text)
        text += word.text()
        textend = len(text)

        nodes_seqnr += 1
        map_id_to_nodenr[word.id] = nodes_seqnr


        tokens.append(
            E.nodes({
                    "{http://www.omg.org/XMI}type": "sDocumentStructure:SToken",
                    },
                    *convert_identifier(word, **kwargs),
                    *convert_type_information(word, **kwargs),
                    *convert_common_attributes(word,token_namespace, **kwargs),
                    *convert_inline_annotations(word, **kwargs)
            )
        )


        textrelations.append(
            E.edges({
                    "{http://www.omg.org/XMI}type": "sDocumentStructure:STextualRelation",
                    "source": f"//@nodes.{nodes_seqnr}",
                    "target": "//@nodes.0"
                    },
                    E.labels({
                        "{http://www.omg.org/XMI}type": "saltCore:SElementId",
                        "namespace": "salt",
                        "name": "id",
                        "value": "T::salt:" + kwargs['corpusprefix'] + "/" + doc.id + '#sTextRel' + str(len(textrelations)+1)
                    }),
                    E.labels({
                        "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SNAME",
                        "value": "T::sTextRel" + str(len(textrelations)+1)
                    }),
                    E.labels({
                        "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SSTART",
                        "value": f"N::{textstart}"
                    }),
                    E.labels({
                        "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                        "namespace": "salt",
                        "name": "SEND",
                        "value": f"N::{textend}"
                    })
            )
        )

        if word.space or (prevword and word.parent != prevword.parent):
            text += " "

        prevword = word

    return (tokens, textrelations, text, map_id_to_nodenr, nodes_seqnr)

def convert_inline_annotations(word, **kwargs):
    """Convert FoLiA inline annotations to salt SAnnotation labels on a token"""
    for annotation in word.select(folia.AbstractInlineAnnotation):
        if kwargs['saltnamespace'] and (annotation.set is None or annotation.set == word.doc.defaultset(annotation.ANNOTATIONTYPE)):
           #add a simplified annotation in the Salt namespace, this facilitates
           #conversion to other formats
           yield E.labels({
                       "{http://www.omg.org/XMI}type": "saltCore:SAnnotation",
                       "namespace": "salt",
                       "name": annotation.XMLTAG,
                       "value": "T::" + annotation.cls
                   })

        if not kwargs['saltonly']:
            namespace = "FoLiA::" + annotation.XMLTAG + "::" + (annotation.set if annotation.set else "")

            for x in convert_common_attributes(annotation, namespace, **kwargs):
                yield x

            for x in convert_features(annotation, namespace, **kwargs):
                yield x

            for x in convert_higher_order(annotation, namespace, **kwargs):
                yield x

def convert_structure_annotations(doc, map_id_to_nodenr, nodes_seqnr, **kwargs):
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
                namespace = "FoLiA::" + structure.XMLTAG + "::" + (structure.set if structure.set else "")
                nodes_seqnr += 1
                structure_nodes.append(
                        E.nodes({
                            "{http://www.omg.org/XMI}type": "sDocumentStructure:SSpan",
                            },
                            E.labels({ #we follow the example of the TCF->Salt converter here where it is used for sentences, a bit of weird entry, hopefully they knew what they were doing and this triggers some special behaviour for some of the converters? I just made it a bit more generic so it works for all structure types.
                                "{http://www.omg.org/XMI}type": "saltCore:SAnnotation",
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
                                "{http://www.omg.org/XMI}type": "sDocumentStructure:SSpanningRelation",
                                 "source": f"//@nodes.{nodes_seqnr}", #the structure
                                 "target": f"//@nodes.{nodenr}", #the token in the span
                             },
                             E.labels({
                                "{http://www.omg.org/XMI}type": "saltCore:SElementId",
                                "namespace": "salt",
                                "name": "id",
                                "value": "T::salt:" + kwargs['corpusprefix'] + "/" + doc.id + '#sStructureSpanRel' + str(len(structure_spanningrelations)+1)
                            }),
                            E.labels({
                                "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                                "namespace": "salt",
                                "name": "SNAME",
                                "value": "T::sStructureSpanRel" + str(len(structure_spanningrelations)+1)
                            }),
                        )
                    )
    return (structure_nodes, structure_spanningrelations, nodes_seqnr)

def convert_span_annotations(doc, map_id_to_nodenr, nodes_seqnr, **kwargs):
    """Convert FoLiA span annotations (sentences, paragraphs, etc) to salt SSpan nodes and SSpaningRelation edges.
    In this conversion the span annotations directly reference the underlying tokens, rather than other underlying structural elements like FoLiA does.
    """

    span_nodes = []
    span_spanningrelations = []
    #Create spans and text relations for all span elements:
    #only handles simple span elements that do not take span roles
    for span in doc.select(folia.AbstractSpanAnnotation):
        if not any((isinstance(x, folia.AbstractSpanRole) for x in span.ACCEPTED_DATA)):
            span_token_nodes = [ map_id_to_nodenr[w.id] for w in span.wrefs() ]
            if span_token_nodes:
                namespace = "FoLiA::" + span.XMLTAG + "::" + (span.set if span.set else "")
                nodes_seqnr += 1
                span_nodes.append(
                        E.nodes({
                            "{http://www.omg.org/XMI}type": "sDocumentspan:SSpan",
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
                                "{http://www.omg.org/XMI}type": "sDocumentspan:SSpanningRelation",
                                 "source": f"//@nodes.{nodes_seqnr}", #the span
                                 "target": f"//@nodes.{nodenr}", #the token in the span
                             },
                             E.labels({
                                "{http://www.omg.org/XMI}type": "saltCore:SElementId",
                                "namespace": "salt",
                                "name": "id",
                                "value": "T::salt:" + kwargs['corpusprefix'] + "/" + doc.id + '#sSpanRel' + str(len(span_spanningrelations)+1)
                            }),
                            E.labels({
                                "{http://www.omg.org/XMI}type": "saltCore:SFeature",
                                "namespace": "salt",
                                "name": "SNAME",
                                "value": "T::sSpanRel" + str(len(span_spanningrelations)+1)
                            })
                        )
                    )
    return (span_nodes, span_spanningrelations, nodes_seqnr)


def convert_identifier(annotation, **kwargs):
    if annotation.id:
        yield E.labels({
            "{http://www.omg.org/XMI}type": "saltCore:SElementId",
            "namespace": "salt",
            "name": "id",
            "value": "T::salt:" + kwargs['corpusprefix'] + "/" + annotation.doc.id + '#' + annotation.id
        })
        yield E.labels({
            "{http://www.omg.org/XMI}type": "saltCore:SFeature",
            "namespace": "salt",
            "name": "SNAME",
            "value": "T::" + annotation.id
        })

def convert_type_information(annotation, **kwargs):
    """Adds extra FoLiA type information as SMetaAnnotation labels (on salt nodes)"""
    if annotation.XMLTAG:
        yield E.labels({
            "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
            "namespace": "FoLiA",
            "name": "elementtype",
            "value": "T::" + annotation.XMLTAG
        })
    if annotation.ANNOTATIONTYPE:
        yield E.labels({
            "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
            "namespace": "FoLiA",
            "name": "annotationtype",
            "value": "T::" + folia.annotationtype2str(annotation.ANNOTATIONTYPE).lower()
        })

def convert_common_attributes(annotation,namespace, **kwargs):
    """Convert common FoLiA attributes as salt SMetaAnnotation labels (on salt nodes)"""

    if annotation.cls is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SAnnotation",
                    "namespace": namespace,
                    "name": "class",
                    "value": "T::" + annotation.cls
                })

    if annotation.id is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "id",
                    "value": "T::" + annotation.id
                })

    if annotation.confidence is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "confidence",
                    "value": "N::" + str(annotation.confidence)
                })

    if annotation.n is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "n",
                    "value": "T::" + annotation.n
                })

    if annotation.href is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "href",
                    "value": "T::" + annotation.href
                })

    if annotation.datetime is not None:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "datetime",
                    "value": "T::" + annotation.datetime.strftime("%Y-%m-%dT%H:%M:%S") #MAYBE TODO: I'm not sure if XMI/salt has a specific date type possibly?
                })


    if annotation.processor:
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "processor/id",
                    "value": "T::" + annotation.processor.id
                })
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "processor/name",
                    "value": "T::" + annotation.processor.name
                })
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "processor/type",
                    "value": "T::" + annotation.processor.type
                })

def convert_features(annotation, namespace, **kwargs):
    """Convert FoLiA features to SAnnotation labels (on salt nodes)"""
    for feature in annotation.select(folia.Feature, recursive=False):
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SAnnotation",
                    "namespace": namespace,
                    "name": "feature/" + feature.subset,
                    "value": "T::" + feature.cls
                })

def convert_higher_order(annotation, namespace, **kwargs):
    """Convert certain FoLiA higher-order features to SAnnotation labels (on salt nodes)"""
    for seqnr, description in enumerate(annotation.select(folia.Description, recursive=False)):
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "description/" + str(seqnr + 1),
                    "value": "T::" + description.value
                })

    for seqnr, comment in enumerate(annotation.select(folia.Comment, recursive=False)):
        yield E.labels({
                    "{http://www.omg.org/XMI}type": "saltCore:SMetaAnnotation",
                    "namespace": namespace,
                    "name": "comment/" + str(seqnr + 1),
                    "value": "T::" + description.value
                })



def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('--recurse','-r',help="recurse into subdirectories", action='store_true', required=False)
    parser.add_argument('--extension','-e',type=str, help="extension", action='store', default="xml",required=False)
    parser.add_argument('--corpusprefix',type=str, help="Corpus prefix for salt", action='store', default="/corpus",required=False)
    parser.add_argument('--saltnamespace','-s',help="Add simplified annotations in the salt namespace", action='store_true', required=False, default=False)
    parser.add_argument('--saltonly','-S',help="Skip complex annotations not in the salt namespace (use with --saltnamespace). This will ignore a lot of the information FoLiA provides!", action='store_true', required=False, default=False)
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

#!/usr/bin/env python3

"""
Converts the FoLiA specification to an RDF schema.
"""

import argparse
import yaml
import sys
from collections import defaultdict

BOOLPROPERTIES = ('printable','speakable','hidden','xlink','textcontainer','phoncontainer','implicitspace','auth','primaryelement','auto_generate_id','setonly','wrefable')
STRINGPROPERTIES = ('subset','textdelimiter')

def getelements(d: dict):
    elements = []
    elementdict = {} #flat (unnested) dictionary
    parents = defaultdict(list)
    if 'elements' in d:
        for e in d['elements']:
            elementdict[e['class']] = e
            elements.append(e)
            children, elementdict2, parents2 = getelements(e)
            elementdict.update(elementdict2)
            parents.update(parents2)
            elements += children
            for c in children:
                if e['class'] not in parents[c['class']]:
                    parents[c['class']].append(e['class'])
    return (elements, elementdict, parents)

def addfromparents(spec, elementdict, parents, elementname, key):
    try:
        value = set(spec['defaultproperties'][key])
    except TypeError:
        value = set()
    if 'properties' in elementdict[elementname] and key in elementdict[elementname]['properties'] and elementdict[elementname]['properties'][key]:
        value |= set(elementdict[elementname]['properties'][key])
    else:
        value |= set()
    for parent in parents[elementname]:
        value |= addfromparents(spec, elementdict, parents, parent, key)
    return value

def norm_annotationtype(s):
    """Normalize the annotation type for use in URIs"""
    return s[0] + s[1:].lower() + "AnnotationType"

def norm_attribute(s):
    """Normalize the attribute for use in URIs"""
    return s[0] + s[1:].lower() + "Attribute"

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--specification', type=str,help="Point this to the FoLiA Specification YAML", action='store',default="folia/schemas/folia.yml",required=True)
    parser.add_argument('-v','--version',help="Output the version of the FoLiA specification", action='store_true',required=False)
    args = parser.parse_args()


    #Load specification
    with open(args.specification,'r',encoding='utf-8') as f:
        spec = yaml.load(f, Loader=yaml.FullLoader)

    if args.version:
        print("FoLiA specification is at version v" + spec['version'],file=sys.stderr)
        sys.exit(0)

    elements, elementdict, parents = getelements(spec) #gathers all class names
    elements.sort(key=lambda x: x['class'])

    print(\
f"""@prefix folia: <{spec['namespace']}#> .
@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix xs: <http://www.w3.org/2001/XMLSchema#> .
@prefix dc: <http://purl.org/dc/elements/1.1/#> .

### Concept Schemes ###

folia:AnnotationTypes a skos:ConceptScheme ;
                      dc:title "FoLiA Annotation Types" ;
                      dc:description "Defines the annotation types of FoLiA, this includes linguistic, structural and markup annotation types" .
folia:AnnotationType a rdfs:Class .

folia:Attributes a skos:ConceptScheme ;
                 dc:title "FoLiA Attributes" ;
                 dc:description "Defines common attributes on FoLiA elements." .
folia:Attribute a rdfs:Class .

folia:Elements a skos:ConceptScheme ;
                 dc:title "FoLiA Elements" ;
                 dc:description "Defines FoLiA elements. These correspond to element in FoLiA XML" .
folia:Element  a rdfs:Class .

### Element Properties ###

folia:xmltag a rdf::Property ;
             rdfs:domain folia:Element ;
             rdfs:range xs:NCName .
folia::annotationtype a rdf::Property ;
                      rdfs:domain folia:Element ;
                      rdfs:range folia:AnnotationType .
folia:occurrences a rdf:Property ;
                    rdfs:domain folia:element ;
                    rdfs:range xs:integer .
folia:occurrences_per_set a rdf:Property ;
                          rdfs:domain folia:element ;
                          rdfs:range xs:integer .
folia:subset a rdf:Property ;
               rdfs:domain folia:Element .
folia:textdelimiter a rdf:Property ;
                    rdfs:domain folia:Element ;
                    rdfs:range xs:string .
folia:requireAttribute a rdf::Property ;
                       rdfs:domain folia:Element ;
                       rdfs:range folia:Attribute .
folia:optionalAttribute a rdf::Property ;
                       rdfs:domain folia:Element ;
                       rdfs:range folia:Attribute .
folia:acceptedElement a rdf:Property ;
                      rdfs:domain folia:Element ;
                      rdfs:range folia:Element .

""")

    for prop in BOOLPROPERTIES:
        print()
        print(f"folia:{prop} a rdf:Property ;")
        print("     rdfs:domain folia:Element ;")
        print("     rdfs:range xs:bool .")

    print("\n### Annotation Types ###\n""")

    for annotationtype in spec['annotationtype']:
        print()
        annotationtype_rdf = norm_annotationtype(annotationtype)
        predicates = []
        print(f"folia:{annotationtype_rdf} a skos:Concept, folia:AnnotationType ;")
        predicates.append("skos:inScheme folia:AnnotationTypes")
        docprops = spec['annotationtype_doc'].get(annotationtype.lower(),{})
        for i, (key, value) in enumerate(docprops.items()):
            if key == "name":
                predicates.append(f"skos:prefLabel \"{value}\"")
            elif key == "description":
                predicates.append(f"skos:definition \"{value}\"")
            elif key == "history":
                predicates.append(f"skos:historyNote \"{value}\"")
        printpredicates(predicates)

    print("\n### Attributes ###\n""")

    for attribute in spec['attributes']:
        print()
        attribute_rdf = norm_attribute(attribute)
        predicates = []
        print(f"folia:{attribute_rdf} a skos:Concept, folia:Attribute ;")
        predicates.append("skos:inScheme folia:Attributes")
        for key, value in spec['attributes_doc'].get(attribute.lower(),{}).items():
            if key == "name":
                predicates.append(f"skos:prefLabel \"{value}\"")
            elif key == "description":
                predicates.append(f"skos:definition \"{value}\"")
            elif key == "history":
                predicates.append(f"skos:historyNote \"{value}\"")
        printpredicates(predicates)

    print("\n### Elements ###\n""")
    print()

    for _elementkey, element in sorted(elementdict.items()):
        c = element['class']
        print()
        predicates = []
        print(f"folia:{c} a skos:Concept, folia:Element ;")
        predicates.append("skos:inScheme folia:Elements")
        if c in parents:
            for parent in parents[c]:
                predicates.append(f"rdfs:subClassOf folia:{parent}")
                predicates.append(f"skos:broader folia:{parent}") #A has broader concept B
        if 'properties' in element:
            for key,value in element['properties'].items():
                if key == "label" and value:
                    predicates.append(f"skos:prefLabel \"{value}\"")
                elif key == "xmltag" and value:
                    predicates.append(f"folia:xmltag \"{value}\"")
                    predicates.append(f"skos:altLabel \"{value}\"")
                elif key == "subset" and value:
                    predicates.append(f"folia:subset \"{value}\"")
                elif key == "statements":
                    value = norm_annotationtype(value)
                    predicates.append(f"folia:annotationtype folia:{value}")
                elif key in BOOLPROPERTIES:
                    if value:
                        value = "true"
                    else:
                        value = "false"
                    predicates.append(f"folia:{key} \"{value}\"")
                elif key in STRINGPROPERTIES:
                    if not value: value = ""
                    value = value.replace("\n","\\n")
                    predicates.append(f"folia:{key} \"{value}\"")
                elif key == 'required_attribs' and value:
                    assert isinstance(value, list)
                    for value in value:
                        value = norm_attribute(value)
                        predicates.append(f"folia:requireAttribute folia:{value}")
                elif key == 'optional_attribs' and value:
                    assert isinstance(value, list)
                    for value in value:
                        value = norm_attribute(value)
                        predicates.append(f"folia:optionalAttribute folia:{value}")
                elif key == 'accepted_data' and value:
                    for value in value:
                        predicates.append(f"folia:acceptedElement folia:{value}")
        printpredicates(predicates)



def printpredicates(predicates):
    print(" ;\n".join([ (" " * 8) + x for x in predicates]) + " .")


if __name__ == '__main__':
    main()

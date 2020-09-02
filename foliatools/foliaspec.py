#!/usr/bin/env python3

"""
Tool to adapt library sources and documentation according to the latest FoLiA specification. Filenames are Python, C++ or ReStructuredText files that may contain foliaspec instructions, the files will be updated according to the latest specification. This tool is mostly for internal use and of less interest to the general ppublic.
"""

from __future__ import print_function, unicode_literals, division, absolute_import #python 2.7 compatibility

import sys
import datetime
import os
import argparse
from collections import defaultdict, OrderedDict
import yaml

skip_properties = {
    'c++': ('primaryelement',), #these are not handled in libfolia, or handled differently, don't output these in the source
}




#global variables
parents = defaultdict(list)
elementdict = {} #flat (unnested) dictionary
spec = {}
elements = []
elementnames = []

def getelements(d):
    elements = []
    if 'elements' in d:
        for e in d['elements']:
            elementdict[e['class']] = e
            elements.append(e)
            children = getelements(e)
            elements += children
            for c in children:
                if e['class'] not in parents[c['class']]:
                    parents[c['class']].append(e['class'])
    return elements



################################################################

def addfromparents(elementname, key):
    try:
        value = set(spec['defaultproperties'][key])
    except TypeError:
        value = set()
    if 'properties' in elementdict[elementname] and key in elementdict[elementname]['properties'] and elementdict[elementname]['properties'][key]:
        value |= set(elementdict[elementname]['properties'][key])
    else:
        value |= set()
    for parent in parents[elementname]:
        value |= addfromparents(parent, key)
    return value


def getbyannotationtype(annotationtype):
    for element in elements:
        if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties'] and element['properties']['annotationtype'].upper() == annotationtype.upper():
            if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
            return element
    raise KeyError("No such annotationtype: " + annotationtype)

def annotationtype2xml(annotationtype):
    """Return the XML tag (str) of the primary element given an annotation type"""
    element = getbyannotationtype(annotationtype)
    return element['properties']['xmltag']

def annotationtype2class(annotationtype):
    """Return the Library Class (str) of the primary element given an annotation type"""
    element = getbyannotationtype(annotationtype)
    return element['class']

def annotationtype2category(annotationtype):
    """Return the category (INLINE, SPAN, MARKUP, HIGHERORDER) given an annotationtype (str)"""
    abstractclass2category = {}
    for key, category in spec['categories'].items():
        if 'class' in category:
            abstractclass2category[category['class']] = key
    element = getbyannotationtype(annotationtype)
    if element['class'] in abstractclass2category:
        return abstractclass2category[element['class']]
    else:
        for parent_class in parents[element['class']]:
            element = elementdict[parent_class]
            if element['class'] in abstractclass2category:
                return abstractclass2category[element['class']]


def outputvar(var, value, target, declare = False):
    """Output a variable ``var`` with value ``value`` in the specified target language."""

    #do we need to quote the value? (bool)
    varname = var.split('.')[-1]

    if isinstance(value, str) and varname.upper() in ('ACCEPTED_DATA','REQUIRED_DATA','REQUIRED_ATTRIBS', 'OPTIONAL_ATTRIBS','ANNOTATIONTYPE'):
        quote = False
    else:
        quote = True


    if isinstance(value, str):
        value = value.replace("\n","\\n").replace("\t","\\t")

    if target == 'python':
        if varname == 'ANNOTATIONTYPE' and isinstance(value,str):
            value = 'AnnotationType.' + value

        if value is None:
            return var + ' = None'
        elif isinstance(value, bool):
            if value:
                return var + ' = True'
            else:
                return var + ' = False'
        elif isinstance(value, (int, float) ):
            return var + ' = ' + str(value)
        elif isinstance(value, (list,tuple,set) ):
            if varname in ('ACCEPTED_DATA','REQUIRED_DATA') or  all([ x in elementnames for x in value ]):
                return var + ' = (' + ', '.join(value) + ',)'
            elif all([ x in spec['attributes'] for x in value ]):
                return var + ' = (' + ', '.join(['Attrib.' + x for x in value]) + ',)'

            if len(value) == 0:
                return var + ' = ()'

            #list items are  enums or classes, never string literals
            if quote:
                return var + ' = (' + ', '.join([ '"' + x + '"' for x in value]) + ',)'
            else:
                return var + ' = (' + ', '.join(value) + ',)'
        else:
            if quote:
                return var + ' = "' + value  + '"'
            else:
                return var + ' = ' + value
    elif target == 'c++':
        typedeclaration = ''
        if value is None:
            if declare: raise NotImplementedError("Declare not supported for None values")
            if varname in ('REQUIRED_ATTRIBS','OPTIONAL_ATTRIBS'):
                return var + ' = NO_ATT;'
            elif varname == 'ANNOTATIONTYPE':
                return var + ' = AnnotationType::NO_ANN;'
            elif varname in ('XMLTAG','TEXTDELIMITER'):
                return var + ' = "NONE";'
            elif varname  == 'REQUIRED_DATA':
                return var + ' = {};'
            elif varname  == 'SUBSET':
                return var + ' = "";'
            else:
                raise NotImplementedError("Don't know how to handle None for " + var)
        elif isinstance(value, bool):
            if declare: typedeclaration = 'const bool '
            if value:
                return typedeclaration + var + ' = true;'
            else:
                return typedeclaration + var + ' = false;'
        elif isinstance(value, int ):
            if declare: typedeclaration = 'const int '
            return typedeclaration + var + ' = ' + str(value) + ';'
        elif isinstance(value, float ):
            if declare: typedeclaration = 'const double '
            return typedeclaration + var + ' = ' + str(value) + ';'
        elif isinstance(value, (list,tuple,set)):
            #list items are  enums or classes, never string literals
            if varname in ('ACCEPTED_DATA','REQUIRED_DATA') or  all([ x in elementnames for x in value ]):
                if declare:
                    typedeclarion = 'const set<ElementType> '
                    operator = '='
                else:
                    typedeclaration = ''
                    operator = '+='
                value = [ x + '_t' for x in value ]
                return typedeclaration + var + ' ' + operator + ' {' + ', '.join(value) + '};'
            elif all([ x in spec['attributes'] for x in value ]):
                return var + ' = ' + '|'.join(value) + ';'
            else:
                return typedeclaration + var + ' = { ' + ', '.join([ '"' + x + '"' for x in value if x]) + ', };'
        else:
            if varname == 'ANNOTATIONTYPE':
                value = "AnnotationType::" + value

            if quote:
                if declare: typedeclaration = 'const string '
                return typedeclaration + var + ' = "' + value+ '";'
            else:
                if declare: typedeclaration = 'const auto '
                return typedeclaration + var + ' = ' + value+ ';'
    elif target == 'rust':
        typedeclaration = ''
        prefix = ''
        if value is None:
            if declare: raise NotImplementedError("Declare not supported for None values")
            if varname in ('required_attribs','optional_attribs','required_data','accepted_data'):
                return var + ' = &[];'
            elif varname in ('xmltag'):
                return var + ' = "";'
            elif varname in ('textdelimiter', 'annotationtype','subset'):
                return var + ' = None;'
            else:
                raise NotImplementedError("Don't know how to handle None for " + var)
        elif isinstance(value, bool):
            if declare:
                typedeclaration = ': bool'
                prefix = 'let '
            if value:
                return prefix + var + typedeclaration + ' = true;'
            else:
                return prefix + var + typedeclaration + ' = false;'
        elif isinstance(value, int ):
            if declare:
                typedeclaration = ': i32'
                prefix = 'let '
            return prefix + var + typedeclaration + ' = ' + str(value) + ';'
        elif isinstance(value, float ):
            if declare:
                typedeclaration = ': f64'
                prefix = 'let '
            return prefix + var + typedeclaration + ' = ' + str(value) + ';'
        elif isinstance(value, (list,tuple,set)):
            #list items are  enums or classes, never string literals
            if varname in ('accepted_data','required_data') or  all([ x in elementnames for x in value ]):
                if declare:
                    typedeclarion = ": &'static [AcceptedData] "
                    operator = '='
                    prefix = 'let '
                else:
                    typedeclaration = ''
                    operator = '='
                    prefix = ''
                value = [ accepteddata_rust(x) for x in value ]
                return prefix + var + typedeclaration + ' ' + operator + ' &[' + ', '.join(value) + '];'
            elif varname in ('optional_attribs', 'required_attribs') or all([ x in spec['attributes'] for x in value ]):
                if declare:
                    typedeclarion = ": &'static [AttribType] "
                    operator = '='
                    prefix = 'let '
                value = [ "AttribType::" + x  for x in value ]
                return prefix + var + typedeclaration + ' = &[ ' + ','.join(value) + ' ];'
            else:
                return prefix + var + typedeclaration + ' = &[ ' + ', '.join([ '"' + x + '"' for x in value if x]) + ', ];'
        else:
            if varname.lower() == 'annotationtype':
                value = "Some(AnnotationType::" + value + ")"
                quote = False
            elif varname in ('textdelimiter', 'subset'):
                value = 'Some("' + value + '")'
                quote = False

            if quote:
                if declare:
                    typedeclaration = ': &str '
                    prefix = 'let '
                return prefix + var + typedeclaration + ' = "' + value+ '";'
            else:
                if declare:
                    typedeclaration = ''
                    prefix = 'let '
                return prefix + var + typedeclaration + ' = ' + value+ ';'
    elif target == 'rst':
        return var + ": " + str(value)

#concise description for all available template blocks
blockhelp = {
        'namespace': 'The FoLiA XML namespace',
        'version': 'The FoLiA version',
        'version_major': 'The FoLiA version (major)',
        'version_minor': 'The FoLiA version (minor)',
        'version_sub': 'The FoLiA version (sub/rev)',
        'attributes': 'Defines all common FoLiA attributes (as part of the Attrib enumeration)',
        'annotationtype': 'Defines all annotation types (as part of the AnnotationType enumeration)',
        'instantiateelementproperties': 'Instantiates all element properties for the first time, setting them to the default properties',
        'setelementproperties': 'Sets all element properties for all elements',
        'annotationtype_string_map': 'A mapping from annotation types to strings',
        'annotationtype_elementtype_map': 'A mapping from annotation types to element types, based on the assumption that there is always only one primary element for an annotation type (and possible multiple secondary ones which are not included in this map,w)',
        'string_annotationtype_map': 'A mapping from strings to annotation types',
        'annotationtype_xml_map': 'A mapping from annotation types to xml tags (strings)',
        'structurescope': 'Structure scope above the sentence level, used by next() and previous() methods',
        'defaultproperties': 'Default properties which all elements inherit',
        'default_ignore': 'Default ignore list for the select() method, do not descend into these',
        'default_ignore_annotations': 'Default ignore list for token annotation',
        'default_ignore_structure': 'Default ignore list for structure annotation',
        'wrefables': 'Elements that act as words and can be referable from span annotations',
}

def setelementproperties_cpp(element,indent, defer,done):
    commentsign = "//"
    target = 'c++'
    s = commentsign + "------ " + element['class'] + " -------\n"
    if element['class'] in parents:
        for parent in parents[element['class']]:
            if parent not in done:
                defer[parent].append(element)
                return None
            else:
                s += indent + element['class'] + '::PROPS = ' + parent + '::PROPS;\n'
            break
    s += indent + element['class'] + '::PROPS.ELEMENT_ID = ' + element['class'] + '_t;\n'
    if 'properties' in element:
        for prop, value in sorted(element['properties'].items()):
            if target not in skip_properties or prop not in skip_properties[target]:
                if prop == 'xmltag':
                    if 'Feature' in parents[element['class']] and 'subset' in element['properties'] and element['properties']['subset']:
                        value = element['properties']['subset']
                elif prop == 'accepted_data':
                    value = tuple(sorted(addfromparents(element['class'],'accepted_data')))
                    if ('textcontainer' in element['properties'] and element['properties']['textcontainer']) or ('phoncontainer' in element['properties'] and element['properties']['phoncontainer']):
                        value += ('XmlText',)
                    if 'WordReference' in value:
                        value += tuple( e  for e in sorted(flattenclasses(spec['wrefables'])) )
                s += indent + outputvar(element['class'] + '::PROPS.' + prop.upper(),  value, target) + '\n'
    done[element['class']] = True
    return s

def accepteddata_rust(elementname):
    if 'Abstract' in elementname:
        return "AcceptedData::AcceptElementGroup(ElementGroup::" + elementname.replace('Abstract','').replace('Annotation','').replace('Element','') + ")"
    else:
        return "AcceptedData::AcceptElementType(ElementType::" + elementname + ")"


def setelementproperties_rust(element,indent, done):
    target = 'rust'
    done[element['class']] = True
    if element['class'].find('Abstract') == -1:
        s = indent + "    ElementType::" + element['class'] + " => {\n"
        s += indent + "        let mut properties = Properties::default();\n"
        properties = {}
        properties.update(spec['defaultproperties'])
        for parent in parents[element['class']]:
            if 'properties' in elementdict[parent]:
                properties.update(elementdict[parent]['properties'])
        for key in properties:
            if key in ('accepted_data','required_data', 'required_attribs','optional_attribs'):
                properties[key] = tuple(sorted(addfromparents(element['class'],key)))
        if 'properties' in element:
            for key in element['properties']:
                if key in ('accepted_data','required_data', 'required_attribs','optional_attribs') and key in element['properties'] and element['properties'][key]:
                    if properties[key]:
                        properties[key] = tuple(sorted(set(properties[key])  | set(element['properties'][key])))
                    else:
                        properties[key] = element['properties'][key]
                else:
                    properties[key] = element['properties'][key]
        for key,value in properties.items():
            s += indent + "        " +  outputvar('properties.' + key.lower(),  value, target) + '\n'
        s += indent + "        properties\n"
        s += indent + "    },\n"
        return s



def flattenclasses(candidates):
    done = {}
    resolved = set()
    for c in candidates:
        for child, parentlist in parents.items():
            if c in parentlist:
                if child not in done and child not in candidates:
                    candidates.append(child)
        if c[:8] != 'Abstract':
            resolved.add(c)
    return resolved




def outputblock(block, target, varname, args, indent = ""):
    """Output the template block (identified by ``block``) for the target language"""

    if target == 'python':
        commentsign = '#'
    elif target in ('c++','rust'):
        commentsign = '//'
    elif target == 'rst':
        commentsign = '.. '
    else:
        raise NotImplementedError("Unknown target language: " + target)

    if block in blockhelp:
        s = indent + commentsign + blockhelp[block] + "\n" #output what each block does
    else:
        s = ''

    if block == 'header':
        s += indent + commentsign + "This file was last updated according to the FoLiA specification for version " + str(spec['version']) + " on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ", using foliaspec.py\n"
        s += indent + commentsign + "Code blocks after a foliaspec comment (until the next newline) are automatically generated. **DO NOT EDIT THOSE** and **DO NOT REMOVE ANY FOLIASPEC COMMENTS** !!!"
    elif block == 'version_major':
        versionfields = [ int(x) for x in spec['version'].split('.') ]
        s += indent + outputvar(varname, versionfields[0], target, True)
    elif block == 'version_minor':
        versionfields = [ int(x) for x in spec['version'].split('.') ]
        s += indent + outputvar(varname, versionfields[1] if len(versionfields) > 1 else 0, target, True)
    elif block == 'version_sub' or block == 'version_rev':
        versionfields = [ int(x) for x in spec['version'].split('.') ]
        s += indent + outputvar(varname, versionfields[2] if len(versionfields) > 2 else 0, target, True)
    elif block == 'attributes':
        if target == 'python':
            s += indent + "class Attrib:\n"
            s += indent + "    " +  ", ".join(spec['attributes']) + " = range(" + str(len(spec['attributes'])) + ")"
        elif target == 'c++':
            s += indent + "enum Attrib : int { NO_ATT=0, ///<No attribute\n"
            value = 1
            for attrib in spec['attributes']:
                s +=  attrib + '=' + str(value) + ', '
                if attrib.lower() in spec['attributes_doc']:
                    s += " ///<" + spec['attributes_doc'][attrib.lower()]['name'] + ': ' +  spec['attributes_doc'][attrib.lower()]['description'] + "\n"
                else:
                    s += "\n"
                value *= 2
            s += 'ALL='+str(value) + ' };'
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'elementtype':
        if target == 'c++':
            s += indent + "enum ElementType : unsigned int { BASE=0,"
            s += ", ".join([ e + '_t' for e in elementnames]) + ", PlaceHolder_t, XmlComment_t, XmlText_t,  LastElement };\n"
        elif target == 'rust':
            s += indent + "pub enum ElementType { " + ", ".join([ e for e in elementnames if not e.startswith('Abstract')]) + " }\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'elementgroup':
        if target == 'rust':
            s += indent + "pub enum ElementGroup { " + ", ".join([ e.replace('Abstract','').replace('Annotation','').replace('Element','') for e in elementnames if e.startswith('Abstract') or e == 'Feature'] ) + " }\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype':
        if target == 'python':
            s += indent + "class AnnotationType:\n"
            s += indent + "    " +  ", ".join(spec['annotationtype']) + " = range(" + str(len(spec['annotationtype'])) + ")"
        elif target == 'c++':
            s += indent + "enum AnnotationType : int { NO_ANN, ///<No type dummy\n"
            for t in spec['annotationtype']:
                s += "    " + t + ","
                if t.lower() in spec['annotationtype_doc']:
                    s += " ///<" + spec['annotationtype_doc'][t.lower()]['name'] + ': ' +  spec['annotationtype_doc'][t.lower()]['description'] + "\n"
                else:
                    s += "\n"
            s += "LAST_ANN };\n"
        elif target == 'rust':
            s += indent + "pub enum AnnotationType { " + ", ".join(spec['annotationtype']) + " }\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'defaultproperties':
        if target == 'c++':
            s += indent + "ELEMENT_ID = BASE;\n"
            s += indent + "ACCEPTED_DATA.insert(XmlComment_t);\n"
            for prop, value in sorted(spec['defaultproperties'].items()):
                if target not in skip_properties or prop not in skip_properties[target]:
                    s += indent + outputvar( prop.upper(),  value, target) + '\n'
        elif target == 'python':
            for prop, value in sorted(spec['defaultproperties'].items()):
                s += indent + outputvar('AbstractElement.' + prop.upper(),  value, target) + '\n'
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'instantiateelementproperties':
        if target == 'c++':
            for element in elements:
                s += indent + "properties " + element['class'] + '::PROPS = DEFAULT_PROPERTIES;\n'
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'setelementproperties':
        if target == 'python':
            for element in elements:
                s += commentsign + "------ " + element['class'] + " -------\n"
                #s += element['class'].__doc__ =
                if 'properties' in element:
                    for prop, value in sorted(element['properties'].items()):
                        if prop == 'accepted_data':
                            value = tuple(sorted(addfromparents(element['class'],'accepted_data')))
                        s += indent + outputvar(element['class'] + '.' + prop.upper(),  value, target) + '\n'
        elif target == 'c++':
            done = {}
            defer = defaultdict(list) #defer output of some elements until parent elements are processed:  hook => deferred_elements
            for element in elements:
                output = setelementproperties_cpp(element,indent, defer,done)
                if output:
                    s += output
                    if element['class'] in defer:
                        for deferred in defer[element['class']]:
                            s += setelementproperties_cpp(deferred,indent, defer,done)
        elif target == 'rust':
            done = {}
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                output = setelementproperties_rust(element,indent,done)
                if output:
                    s += output
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_string_map':
        if target == 'c++':
            s += indent + "const map<AnnotationType,string> ant_s_map = {\n"
            s += indent + "  { AnnotationType::NO_ANN, \"NONE\" },\n"
            done = {}
            for element in elements:
                if 'properties' in element and  'annotationtype' in element['properties'] and element['properties']['annotationtype'] not in done:
                    #if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "  { AnnotationType::" + element['properties']['annotationtype'] + ',  "' + element['properties']['annotationtype'].lower() + '" },\n'
                    done[element['properties']['annotationtype']] = True #prevent duplicates
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            done = {}
            for element in elements:
                if 'properties' in element and  'annotationtype' in element['properties'] and element['properties']['annotationtype'] not in done:
                    s += indent + "  AnnotationType::" + element['properties']['annotationtype'] + " => \"" + element['properties']['annotationtype'].lower() + "\",\n"
                    done[element['properties']['annotationtype']] = True #prevent duplicates
            s += indent + "}\n"

        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'string_annotationtype_map':
        if target == 'c++':
            s += indent + "const map<string,AnnotationType> s_ant_map = {\n"
            s += indent + "  { \"NONE\", AnnotationType::NO_ANN },\n"
            done = {}
            for element in elements:
                if 'properties' in element and  'annotationtype' in element['properties'] and element['properties']['annotationtype'] not in done:
                    s += indent + '  { "' + element['properties']['annotationtype'].lower() + '", AnnotationType::' + element['properties']['annotationtype'] + ' },\n'
                    done[element['properties']['annotationtype']] = True #prevent duplicates
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            done = {}
            for element in elements:
                if 'properties' in element and  'annotationtype' in element['properties'] and element['properties']['annotationtype'] not in done:
                    s += indent + "    \"" +element['properties']['annotationtype'].lower() + "\" => Some(AnnotationType::" + element['properties']['annotationtype'] + "),\n"
                    done[element['properties']['annotationtype']] = True #prevent duplicates
            s += indent + "    _ => None\n"
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_xml_map':
        if target == 'python':
            s += indent + "ANNOTATIONTYPE2XML = {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "    AnnotationType." + element['properties']['annotationtype'] + ':  "' + element['properties']['xmltag'] + '" ,\n'
            s += indent + "}"
        elif target == 'c++':
            s += indent + "const map<AnnotationType,string> annotationtype_xml_map = {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "  {  AnnotationType::" + element['properties']['annotationtype'] + ', "' + element['properties']['xmltag'] + '" },\n'
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "  AnnotationType::" + element['properties']['annotationtype'] + ' => "' + element['properties']['xmltag'] + '",\n'
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_elementtype_map':
        if target == 'c++':
            s += indent + "const map<AnnotationType,ElementType> annotationtype_elementtype_map = {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "  {  AnnotationType::" + element['properties']['annotationtype'] + ', ' + element['class'] + '_t },\n'
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    if 'primaryelement' in element['properties'] and not element['properties']['primaryelement']: continue #not primary, skip
                    s += indent + "    AnnotationType::" + element['properties']['annotationtype'] + ' => ElementType::' + element['class'] + ',\n'
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)

    elif block == 'elementtype_annotationtype_map':
        if target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                    s += indent + "    ElementType::" + element['class'] + " => Some(AnnotationType::" + element['properties']['annotationtype'] + "),\n"
            s += indent + "    _ => None\n"
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'elementgroup_elementtypes_map':
        if target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'elements' in element:
                    s += indent + "    ElementGroup::" + element['class'].replace("Abstract","").replace("Annotation","").replace("Element","") + " => &[" + ",".join([ "ElementType::" + subelement['class'] for subelement in element['elements'] if subelement['class'].find('Abstract') == -1 ] ) + "],\n"
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)

    elif block == 'elementtype_string_map':
        if target == 'c++':
            s += indent + "const map<ElementType,string> et_s_map = {\n"
            s += indent + "  { BASE, \"FoLiA\" },\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag']:
                    s += indent + "  { " + element['class'] + '_t,  "' + element['properties']['xmltag'] + '" },\n'
                elif 'properties' in element and 'subset' in element['properties'] and element['properties']['subset']:
                    if element['class'] == 'HeadFeature':
                        s += indent + "  { HeadFeature_t,  \"headfeature\" },\n"
                    else:
                        s += indent + "  { " + element['class'] + '_t,  "' + element['properties']['subset'] + '" },\n'
                else:
                    s += indent + "  { " + element['class'] + '_t,  "_' + element['class'] + '" },\n'
            s += indent + '  { PlaceHolder_t, "_PlaceHolder" },\n'
            s += indent + '  { XmlComment_t, "_XmlComment" },\n'
            s += indent + '  { XmlText_t, "_XmlText" }\n'
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag']:
                    s += indent + "  ElementType::" + element['class'] + ' => "' + element['properties']['xmltag'] + '",\n'
                elif 'properties' in element and 'subset' in element['properties'] and element['properties']['subset']:
                    if element['class'] == 'HeadFeature':
                        s += indent + '  ElementType::HeadFeature => "headfeature",\n'
                    else:
                        s += indent + "  ElementType::" + element['class'] + ' => "' + element['properties']['subset'] + '",\n'
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'string_elementtype_map':
        if target == 'c++':
            s += indent + "const map<string,ElementType> s_et_map = {\n"
            s += indent + "  { \"FoLiA\", BASE },\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag']:
                    s += indent + '  { "' + element['properties']['xmltag'] + '", ' + element['class'] + '_t  },\n'
                elif 'properties' in element and 'subset' in element['properties'] and element['properties']['subset']:
                    if element['class'] == 'HeadFeature':
                        s += indent + "  { \"headfeature\", HeadFeature_t },\n"
                    else:
                        s += indent + '  { "' + element['properties']['subset'] + '", ' + element['class'] + '_t  },\n'
                else:
                    s += indent + '  { "_' + element['class'] + '", ' + element['class'] + '_t  },\n'
            s += indent + '  { "_PlaceHolder", PlaceHolder_t  },\n'
            s += indent + '  { "_XmlComment", XmlComment_t  },\n'
            s += indent + '  { "_XmlText", XmlText_t  }\n'
            s += indent + "};\n"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag']:
                    s += indent + '  "' + element['properties']['xmltag'] + '" =>  Ok(ElementType::' + element['class'] + '),\n'
                elif 'properties' in element and 'subset' in element['properties'] and element['properties']['subset']:
                    if element['class'] == 'HeadFeature':
                        s += indent + '  "headfeature" =>  Ok(ElementType::' + element['class'] + '),\n'
                    else:
                        s += indent + '  "' + element['properties']['subset'] + '" =>  Ok(ElementType::' + element['class'] + '),\n'
            s += indent + '    _ => Err(FoliaError::ParseError(format!("Unknown tag has no associated element type: {}",tag).to_string()))\n'
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'string_class_map':
        if target == 'python':
            s += indent + "XML2CLASS = {\n"
            for element in elements:
                if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag']:
                    s += indent + '    "' + element['properties']['xmltag'] + '": ' + element['class'] + ',\n'
            s += indent + "}\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'oldtags_map':
        if target == 'python':
            s += indent + "OLDTAGS = {\n"
            for old, new in sorted(spec['oldtags'].items()):
                s += indent + '  "' + old + '": "' + new + '",'
            s += indent + "}\n"
        elif target == 'c++':
            s += indent + "const map<string,string> oldtags = {\n"
            for old, new in sorted(spec['oldtags'].items()):
                s += indent + "  { \"" + old + "\", \"" + new + "\" },\n"
            s += indent + "};"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_layerclass_map':
        if target == 'python':
            s += indent + "ANNOTATIONTYPE2LAYERCLASS = {\n"
            for element in elements:
                if element['class'].endswith('Layer'):
                    if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                        s += indent + "    AnnotationType." + element['properties']['annotationtype'] + ':  ' + element['class'] + ' ,\n'
            s += indent + "    AnnotationType.PREDICATE:  ElementType::SemanticRolesLayer\n"
            s += indent + "}"
        elif target == 'rust':
            s += indent + "match " + args[0] + " {\n"
            for element in elements:
                if element['class'].endswith('Layer'):
                    if 'properties' in element and 'xmltag' in element['properties'] and element['properties']['xmltag'] and 'annotationtype' in element['properties']:
                        s += indent + "    AnnotationType::" + element['properties']['annotationtype'] + ' => Some(ElementType::' + element['class'] + '),\n'
            s += indent + "    AnnotationType::PREDICATE => Some(ElementType::SemanticRolesLayer),\n"
            s += indent + "    _ => None\n"
            s += indent + "}"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'wrefables':
        if target == 'c++':
            s += indent + "const set<ElementType> wrefables = { " + ", ".join([ e + '_t' for e in sorted(flattenclasses(spec['wrefables'])) ]) + " };\n"
        elif target == 'python':
            s += indent + "wrefables = ( " + ", ".join(spec['wrefables']) + ",)\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'default_ignore':
        if target == 'c++':
            s += indent + "const set<ElementType> default_ignore = { " + ", ".join([ e + '_t' for e in sorted(flattenclasses(spec['default_ignore'])) ]) + " };\n"
        elif target == 'python':
            s += indent + "default_ignore = ( " + ", ".join(spec['default_ignore']) + ",)\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'default_ignore_annotations':
        if target == 'c++':
            s += indent + "const set<ElementType> default_ignore_annotations = { " + ", ".join([ e + '_t' for e in sorted(flattenclasses(spec['default_ignore_annotations'])) ]) + " };\n"
        elif target == 'python':
            s += indent + "default_ignore_annotations = ( " + ", ".join(spec['default_ignore_annotations']) + ",)\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'default_ignore_structure':
        if target == 'c++':
            s += indent + "const set<ElementType> default_ignore_structure = { " + ", ".join([ e + '_t' for e in sorted(flattenclasses(spec['default_ignore_structure'])) ]) + " };\n"
        elif target == 'python':
            s += indent + "default_ignore_structure = ( " + ", ".join(spec['default_ignore_structure']) + ",)\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'typehierarchy':
        if target == 'c++':
            s += indent + "static const map<ElementType, set<ElementType> > typeHierarchy = { "
            for child, parentset in sorted(parents.items()):
                s += indent + "   { " + child + '_t' + ", { " + ",".join([p + '_t' for p in parentset ]) + " } },\n"
            s += indent + "   { PlaceHolder_t , { Word_t, AbstractStructureElement_t } }\n"
            s += indent + "};\n";
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'attributefeatures':
        if target == 'c++':
            l = []
            for element in elements:
                if 'properties' in element and 'subset' in element['properties'] and element['properties']['subset']:
                    if element['class'] == 'HeadFeature':
                        l.append("headfeature")
                    else:
                        l.append(element['properties']['subset'])
            l.sort()
            s += indent + "const set<string> AttributeFeatures = { " + ", ".join([ '"' + x + '"' for x in l ]) + " };\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_title':
        if target == 'rst':
            s += spec['annotationtype_doc'][args[0]]['name'] + "\n"
            s += "==================================================================\n"
        elif target in ('c++', 'python'):
            s += indent + commentsign + " " + spec['annotationtype_doc'][args[0]]['name'] + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'annotationtype_description':
        if target == 'rst':
            s += spec['annotationtype_doc'][args[0]]['description'] + "\n"
        elif target in ('c++', 'python'):
            s += indent + commentsign + " " + spec['annotationtype_doc'][args[0]]['description'] + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'specification':
        annotationtype = args[0] #string
        specdata = OrderedDict()
        category = annotationtype2category(annotationtype)
        specdata["Annotation Category"] = ":ref:`" + category +  "_annotation_category`"
        element = getbyannotationtype(annotationtype) #primary element
        required_attribs = addfromparents(element['class'],'required_attribs')
        optional_attribs = addfromparents(element['class'],'optional_attribs')
        if  "CLASS" in required_attribs:
            specdata["Declaration"] = "``<" + annotationtype.lower() + "-annotation set=\"...\">`` *(note: set is mandatory)*"
        elif  "CLASS" in optional_attribs:
            specdata["Declaration"] = "``<" + annotationtype.lower() + "-annotation set=\"...\">`` *(note: set is optional for this annotation type; if you declare this annotation type to be setless you can not assign classes)*"
        else:
            specdata["Declaration"] = "``<" + annotationtype.lower() + "-annotation>`` *(note: there is never a set associated with this annotation type)"
        specdata["Version History"] = spec['annotationtype_doc'][annotationtype.lower()]['history']
        if target == 'rst':
            for key, value in specdata.items():
                s += ":" + key + ": " + value + "\n"
            s += outputblock("specification_element", target, "specification_element", [element['class']])
        elif target in ('c++', 'python'):
            s += indent + commentsign + " Specification:" + "\n"
            for key, value in specdata.items():
                s += indent + commentsign + "  " + key + ": " + value + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'specification_element':
        specdata = OrderedDict()
        for elementclass in args:
            element = elementdict[elementclass] #string
            try:
                annotationtype = element['properties']['annotationtype']
            except KeyError:
                annotationtype = None
            specdata["**Element**"] = "``<" + element['properties']['xmltag'] + ">``"
            specdata["API Class"] = "``" + element['class'] + "`` (`FoLiApy API Reference <https://foliapy.readthedocs.io/en/latest/_autosummary/folia.main." + element['class'] + ".html>`_)"
            required_attribs = addfromparents(element['class'],'required_attribs')
            if "CLASS" in required_attribs: required_attribs.add("SET")
            if "ANNOTATOR" in required_attribs:
                required_attribs.add("ANNOTATORTYPE")
                required_attribs.add("PROCESSOR")
            #print("REQUIRED FOR  " + element['class'], " ".join(required_attribs),file=sys.stderr)
            optional_attribs = addfromparents(element['class'],'optional_attribs')
            if "CLASS" in optional_attribs: optional_attribs.add("SET")
            if "ANNOTATOR" in optional_attribs:
                optional_attribs.add("ANNOTATORTYPE")
                optional_attribs.add("PROCESSOR")
            #print("OPTIONAL FOR  " + element['class'], " ".join(optional_attribs),file=sys.stderr)
            accepted_data = tuple(sorted(addfromparents(element['class'],'accepted_data')))
            if "AbstractSpanRole" in parents[element['class']]:
                specdata["Category "] = "Span Role Element"
            if "AbstractAnnotationLayer" in parents[element['class']]:
                specdata["Category "] = "Layer Element"
            elif "AbstractSpanAnnotation" in parents[element['class']]:
                #find Layer
                layer = "None"
                for e in elements:
                    if e['class'].endswith("Layer") and 'annotationtype' in e['properties'] and e['properties']['annotationtype'] == annotationtype:
                        layer = e['properties']['xmltag']
                specdata["Layer Element"] = "``<" + layer + ">``"
                #Find span roles
                spanroles = []
                for elementname in accepted_data:
                    if "AbstractSpanRole" in parents[elementname]:
                        spanroles.append(elementname)
                spanroles = ", ".join([ "``<" + elementdict[x]['properties']['xmltag'] + ">`` (``" + x + "``)"  for x in spanroles ])
                specdata["Span Role Elements"] = spanroles
            specdata["Required Attributes"] = "\n                      ".join( [ line for line in outputblock("attributes_doc", target, "attributes_doc", ["EMPTY"] + [a.lower() for a in  required_attribs]).split("\n") if line ] )
            if ("xlink" in element["properties"] and element["properties"]["xlink"]) or ("xlink" in elementdict[parents[element["class"]][0]]["properties"] and elementdict[parents[element["class"]][0]]["properties"]["xlink"]):
                xlink  = "\n                      * ``xlink:href`` -- Turns this element into a hyperlink to the specified URL"
                xlink += "\n                      * ``xlink:type`` -- The type of link (you'll want to use ``simple`` in almost all cases)."
            else:
                xlink = ""
            specdata["Optional Attributes"] = "\n                      ".join( [ line for line in outputblock("attributes_doc", target, "attributes_doc", ["EMPTY"] + [a.lower() for a in  optional_attribs]).split("\n") if line ] ) + xlink
            specdata["Accepted Data"] = ", ".join([ "``<" + elementdict[cls]['properties']['xmltag'] + ">`` (:ref:`" + elementdict[cls]['properties']['annotationtype'].lower() + "_annotation`)" for cls in  accepted_data if 'annotationtype' in elementdict[cls]['properties']])
            valid_context = set()
            for e in elements:
                e_accepted_data = addfromparents(e['class'],'accepted_data')
                if element['class'] in e_accepted_data:
                    valid_context.add(e['class'])
            valid_context = tuple(sorted(valid_context))
            specdata["Valid Context"] = ", ".join([ "``<" + elementdict[cls]['properties']['xmltag'] + ">`` (:ref:`" + elementdict[cls]['properties']['annotationtype'].lower() + "_annotation`)" for cls in  valid_context if 'annotationtype' in elementdict[cls]['properties']])
            features = []
            for elementclass in accepted_data:
                if elementclass.endswith("Feature") and elementclass != "Feature":
                    features.append("* ``" + elementdict[elementclass]['properties']['subset'] + "``")
            if features:
                specdata["Feature subsets (extra attributes)"] = "\n                                   ".join( features )
        if target == 'rst':
            for key, value in specdata.items():
                s += ":" + key + ": " + value + "\n"
        elif target in ('c++', 'python'):
            s += indent + commentsign + " Specification:" + "\n"
            for key, value in specdata.items():
                s += indent + commentsign + "  " + key + ": " + value + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'attributes_doc':
        if target == 'rst':
            for attribute, attributedata in spec['attributes_doc'].items():
                if not args or (args and (('group' in attributedata and attributedata['group'] in args) or attribute.lower() in args)):
                    s += "* ``" + attributedata['name'] + "`` -- " + attributedata['description'] + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'toc':
        if target == 'rst':
            for category, categorydata in spec['categories'].items():
                if not args or (args and category in args):
                    s += "* :ref:`" + category + "_annotation_category` --\n  " + categorydata['description'] + "\n" #the first \n is needed otherwise sphinx doesn't produce proper LaTeX, it does not render neither in LaTeX nor HTML
                    for annotationtype in spec['annotationtype']:
                        element = getbyannotationtype(annotationtype)
                        if annotationtype2category(annotationtype) == category:
                            s += "   - :ref:`" + annotationtype.lower() + "_annotation` -- ``<" + element['properties']['xmltag'] +  ">`` -- " + spec['annotationtype_doc'][annotationtype.lower()]['description'] + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'toctree':
        if target == 'rst':
            hidden = 'hidden' in args
            if hidden: args.remove('hidden')
            if args:
                category = args[0]
                s += '.. toctree::\n'
                if hidden:
                    s += '   :hidden:\n'
                s += '   :maxdepth: 3\n\n'
                for annotationtype in spec['annotationtype']:
                    element = getbyannotationtype(annotationtype)
                    if annotationtype2category(annotationtype) == category:
                        s += '   ' + annotationtype.lower() + "_annotation\n"
            else:
                s += '.. toctree::\n'
                if hidden:
                    s += '   :hidden:\n'
                s += '   :includehidden:\n'
                s += '   :maxdepth: 3\n\n'
                for category, categorydata in spec['categories'].items():
                    if category in args:
                        s += '   ' + category + "_annotation_category\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'category_title':
        category = args[0]
        if target == 'rst':
            s += spec['categories'][category]['name'] + "\n"
            s += "===================================================================\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block == 'category_description':
        category = args[0]
        if target == 'rst':
            s += spec['categories'][category]['description'] + "\n"
        else:
            raise NotImplementedError("Block " + block + " not implemented for " + target)
    elif block in spec:
        #simple variable blocks
        s += indent + outputvar(varname, spec[block], target, True)
    else:
        raise Exception("No such block exists in foliaspec: " + block)


    if s and s[-1] != '\n': s += '\n'
    return s


def foliaspec_parser(filename):
    if filename[-2:] in ('.h','.c') or filename[-4:] in ('.cxx','.cpp','.hpp'):
        target = 'c++' #libfolia
        commentsign = '//'
    elif filename[-3:] == '.py':
        target = 'python' #foliapy
        commentsign = '#'
    elif filename[-4:] == '.rst':
        target = 'rst' #folia documentation, reStructuredTexgt
        commentsign = '.. '
    elif filename[-3:] == '.rs':
        target = 'rust' #libfolia-rs
        commentsign = '//'
    else:
        raise Exception("No target language could be deduced from the filename " + filename)

    if not os.path.exists(filename):
        raise FileNotFoundError("File not found: " + filename)

    out = open(filename+'.foliaspec.out','w',encoding='utf-8')


    inblock = False
    blockname = blocktype = ""
    args = []
    indent = ""
    debuglinenum = 0
    debugline = ""
    with open(filename,'r',encoding='utf-8') as f:
        for linenum, line in enumerate(f):
            try:
                strippedline = line.strip()
                if not inblock:
                    if strippedline.startswith(commentsign + 'foliaspec:'):
                        indent = line.find(strippedline) * ' '
                        fields = strippedline[len(commentsign):].split(':')
                        if fields[1] in ('begin','start'):
                            blocktype = 'explicit'
                            blockname = fields[2]
                            try:
                                varname = fields[3]
                            except:
                                varname = blockname
                        elif len(fields) >= 2:
                            blocktype = 'implicit'
                            blockname = fields[1]
                            try:
                                varname = fields[2]
                            except:
                                varname = blockname
                        else:
                            raise Exception("Syntax error: " + strippedline)
                        #are there arguments in the blockname?
                        if blockname[-1] == ')':
                            args = blockname[blockname.find('(') + 1:-1].split(",")
                            blockname = blockname[:blockname.find('(')]
                        else:
                            args = []
                        inblock = True
                        debuglinenum = linenum #used for generating error messages
                        debugline = line
                        out.write(line)
                    elif strippedline.split(' ')[-1].startswith(commentsign + 'foliaspec:'):
                        fields = strippedline.split(' ')[-1][len(commentsign):].split(':')
                        blocktype = 'line'
                        blockname = fields[1]
                        #are there arguments in the blockname?
                        if blockname[-1] == ')':
                            args = blockname[blockname.find('(') + 1:-1].split(",")
                            blockname = blockname[:blockname.find('(')]
                        else:
                            args = []
                        try:
                            varname = fields[2]
                        except:
                            varname = blockname
                        if varname != blockname:
                            out.write( outputblock(blockname, target, varname, args) + " " + commentsign + "foliaspec:" + blockname + ":" + varname + "\n")
                        else:
                            out.write( outputblock(blockname, target, varname, args) + " " + commentsign + "foliaspec:" + blockname + "\n")
                    else:
                        out.write(line)
                else:
                    if not strippedline and blocktype == 'implicit':
                        out.write(outputblock(blockname, target, varname,args,indent) + "\n")
                        inblock = False
                    elif blocktype == 'explicit' and strippedline.startswith(commentsign + 'foliaspec:end:'):
                        out.write(outputblock(blockname, target, varname,args, indent) + "\n" + commentsign + "foliaspec:end:" + blockname + "\n")
                        inblock = False
            except Exception as e:
                print("--- Error processing line " + str(debuglinenum) + " in " + filename + ": " + debugline,file=sys.stderr)
                raise e
    os.rename(filename+'.foliaspec.out', filename)

def usage():
    print("Syntax: foliaspec.py [filename] [filename] ..etc.." ,file=sys.stderr)
    print("",file=sys.stderr)
    sys.exit(0)

def main():
    global spec, elements, elementnames
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s','--specification', type=str,help="Point this to the FoLiA Specification YAML", action='store',default="folia/schemas/folia.yml",required=True)
    parser.add_argument('-v','--version',help="Output the version of the FoLiA specification", action='store_true',required=False)
    parser.add_argument('filenames', nargs='+', help='ReStructuredText files or Python or C++ source code files to process (will modify the files!)')
    args = parser.parse_args()

    if args.version:
        print("FoLiA specification is at version v" + spec['version'],file=sys.stderr)
        sys.exit(0)

    #Load specification
    spec = yaml.load(open(args.specification,'r'))

    elements = getelements(spec) #gathers all class names
    elements.sort(key=lambda x: x['class'])
    elementnames = [ e['class'] for e in elements ]

    for filename in args.filenames:
        print("Processing " + filename,file=sys.stderr)
        foliaspec_parser(filename)

if __name__ == '__main__':
    main()

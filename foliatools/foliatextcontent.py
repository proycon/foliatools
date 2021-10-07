#! /usr/bin/env python
# -*- coding: utf8 -*-

"""
This tool operates on the text redundancy that may occur in FoLiA documents,
i.e. the ability to express the same text on multiple structural levels.
It can remove text redundancy entirely or it can infer text for the higher
(untokenised) levels, adding offset information and mark-up elements if present.

Secondly, the tool may also add text-markup elements for substrings (str element)
(provided there is no overlap).
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import getopt
import sys
import os
import glob
import folia.main as folia
from foliatools import VERSION as TOOLVERSION

def usage():
    print("foliatextcontent",file=sys.stderr)
    print("  by Maarten van Gompel (proycon)",file=sys.stderr)
    print("  Centre for Language and Speech Technology, Radboud University Nijmegen",file=sys.stderr)
    print("  & KNAW Humanities Cluster",file=sys.stderr)
    print("  2015-2021 - Licensed under GPLv3",file=sys.stderr)
    print("",file=sys.stderr)
    print("Description: " + __doc__,file=sys.stderr)
    print("",file=sys.stderr)
    print("Usage: foliatextcontent [options] file-or-dir1 file-or-dir2 ..etc..",file=sys.stderr)
    print("",file=sys.stderr)
    print("Parameters for output:"        ,file=sys.stderr)
    print("  -c                           Clean any text redundancy and retain only text on the deepest level",file=sys.stderr)
    print("  -s                           Add text content on sentence level",file=sys.stderr)
    print("  -p                           Add text content on paragraph level"    ,file=sys.stderr)
    print("  -d                           Add text content on division level",file=sys.stderr)
    print("  -t                           Add text content on global text level"    ,file=sys.stderr)
    print("  -T                           Add text content for the specified elements (comma separated list of folia xml tags)"    ,file=sys.stderr)
    print("  -O                           Add offsets to existing elements of the specified types (comma separated list of folia xml tags). Example: -O w"    ,file=sys.stderr)
    print("  -X                           Do NOT add offset information"    ,file=sys.stderr)
    print("  -F                           Force offsets to refer to the specified structure only (only works if you specified a single element type for -T!!!)"    ,file=sys.stderr)
    print("  -M                           Add substring markup linking to string elements (if any, and when there is no overlap). This also supports strings inside corrections and adds correction markup in that case."    ,file=sys.stderr)
    print("  -e [encoding]                Output encoding (default: utf-8)",file=sys.stderr)
    print("  -w                           Edit file(s) (overwrites input files), will output to stdout otherwise" ,file=sys.stderr)
    print("  -D                           Debug" ,file=sys.stderr)
    print("Parameters for processing directories:",file=sys.stderr)
    print("  -r                           Process recursively",file=sys.stderr)
    print("  -E [extension]               Set extension (default: xml)",file=sys.stderr)


def linkstrings(element, cls='current',debug=False):
    if element.hastext(cls,strict=True) and element.hasannotation(folia.String):
        text = element.textcontent(cls, correctionhandling=folia.CorrectionHandling.EITHER)

        for string in element.select(folia.String, False, True):
            if string.id and debug: print("Found string " + string.id + " (" + cls + ")",file=sys.stderr)
            try:
                stringtextcontent = string.textcontent(cls, correctionhandling=folia.CorrectionHandling.EITHER)
                stringtext = stringtextcontent.text()
                stringoffset = stringtextcontent.offset
            except folia.NoSuchText:
                continue

            if not stringtext:
                continue

            if debug: print("Finding string '" + stringtext + "' in text: ", text.text(), file=sys.stderr)

            if stringoffset is None:
                if debug: print("No offset information found for the text of this string, skipping this one...", file=sys.stderr)
                continue

            offset = 0 #current offset cursor
            length = len(stringtext)
            replaceindex = 0
            replace = []
            for i, subtext in enumerate(text):
                if isinstance(subtext, str):
                    subtextlength = len(subtext)
                    if stringoffset >= offset and stringoffset+length <= offset+subtextlength:
                        reloffset = stringoffset-offset

                        if subtext[reloffset:reloffset+length] != stringtext:
                            print(" String refers to offset " + str(stringoffset) + ", but is not found there ! Found '" + subtext[reloffset:reloffset+length] + "' instead.",file=sys.stderr)
                        else:
                            #match!
                            kwargs = {'processor': element.doc.processor}
                            replaceindex = i
                            if string.id:
                                kwargs['idref'] = string.id
                            markup = folia.TextMarkupString(element.doc, *stringtext, **kwargs)
                            if isinstance(string.parent, folia.AbstractCorrectionChild):
                                correction = string.ancestor(folia.Correction) #does not handle nested annotations, only grabs the deepest one
                                kwargs = {}
                                if correction.id:
                                    kwargs['idref'] = correction.id
                                markup = folia.TextMarkupCorrection(element.doc, markup, idref=correction.id)
                            replace = [subtext[:reloffset], markup, subtext[reloffset+length:]]
                            break

                elif isinstance(subtext, folia.AbstractTextMarkup):
                    subtextlength = len(subtext.text())
                    if stringoffset >= offset and stringoffset+length <= offset+subtextlength:
                        print("String " + str(string.id) + " fits within other markup element ("+str(type(subtext))+"," + str(subtext.id)+ "), not implemented yet", file=sys.stderr)
                        break

                offset += subtextlength

            if replace:
                if debug: print("Replacing item " + str(replaceindex) + " with: ", replace,file=sys.stderr)
                del text.data[replaceindex]
                for x in reversed(replace):
                    if x:
                        text.data.insert(replaceindex,x)
            else:
                if string.id:
                    print("Could not find string " + string.id + " !!!",file=sys.stderr)

def gettextsequence(element, cls, debug=False):
    assert element.PRINTABLE
    if debug: print(" Getting text for ", repr(element),file=sys.stderr)
    if element.TEXTCONTAINER:
        if debug: print("  Found textcontainer ", repr(element), "in", repr(element.ancestor(folia.AbstractStructureElement)),file=sys.stderr)

        if isinstance(element,folia.TextContent) and element.cls != cls:
            if debug: print("  Class mismatch", element.cls,"vs",cls,file=sys.stderr)
            raise StopIteration

        for e in element:
            if isinstance(e, str):
                if debug: print("  Found: ", e,file=sys.stderr)
                yield e, element
            else: #markup (don't recurse)
                if debug: print("  Found markup: ", repr(e),file=sys.stderr)
                yield e, element
                yield e.gettextdelimiter(), None

        yield None,None #Signals a break after this, if we have text content we needn't delve deeper
    else:
        #Do we have a text content?
        foundtext = False
        if debug: print(" Looking for text in ", repr(element),file=sys.stderr)
        for e in element:
            if isinstance(e, folia.TextContent) and e.cls == cls:
                foundtext = True
                for x in gettextsequence(e, cls, debug):
                    yield x
            elif isinstance(e, folia.Correction):
                foundtextincorrection =False
                try:
                    if e.hasnew() and e.new().textcontent(cls):
                        foundtextincorrection = True
                        for x in gettextsequence(e.new().textcontent(cls), cls, debug):
                            yield x
                except folia.NoSuchText:
                    pass
                except folia.NoSuchAnnotation:
                    pass
                if not foundtextincorrection:
                    try:
                        if e.hascurrent() and e.current().textcontent(cls):
                            foundtextincorrection = True
                            for x in gettextsequence(e.current().textcontent(cls), cls, debug):
                                yield x
                    except folia.NoSuchText:
                        pass
                    except folia.NoSuchAnnotation:
                        pass
                if not foundtextincorrection:
                    try:
                        if e.hasoriginal() and e.original().textcontent(cls):
                            foundtextincorrection = True
                            for x in gettextsequence(e.current().textcontent(cls), cls, debug):
                                yield x
                    except folia.NoSuchText:
                        pass
                    except folia.NoSuchAnnotation:
                        pass
                foundtext = foundtextincorrection

        if not foundtext:
            if debug: print(" Looking for text in children of ", repr(element),file=sys.stderr)
            for e in element:
                if e.PRINTABLE and not isinstance(e, folia.String):
                    #abort = False
                    for x in gettextsequence(e, cls, debug):
                        foundtext = True
                        if x[0] is None:
                            #abort = True
                            break
                        yield x
                    #if abort:
                    #    print(" Abort signal received, not processing further elements in ", repr(element),file=sys.stderr)
                    #    break
                if foundtext:
                    delimiter = e.gettextdelimiter()
                    if debug: print(" Got delimiter " + repr(delimiter) + " from " + repr(element), file=sys.stderr)
                    yield e.gettextdelimiter(), None
                elif isinstance(e, folia.AbstractStructureElement) and not isinstance(e, folia.Linebreak) and not isinstance(e, folia.Whitespace):
                    raise folia.NoSuchText("No text was found in the scope of the structure element")


def settext(element, cls='current', offsets=True, forceoffsetref=False, debug=False):
    assert element.PRINTABLE

    if debug: print("In settext for  ", repr(element),file=sys.stderr)

    #get the raw text sequence
    try:
        textsequence = list(gettextsequence(element,cls,debug))
    except folia.NoSuchText:
        return None

    if debug: print("Raw text:  ", textsequence,file=sys.stderr)

    if textsequence:
        newtextsequence = []
        offset = 0
        prevsrc = None
        for i, (e, src) in enumerate(textsequence):
            if e: #filter out empty strings
                if isinstance(e,str):
                    length = len(e)

                    #only whitespace from here on?
                    if not e.strip():
                        onlywhitespace = True
                        for x,y in textsequence[i+1:]:
                            if y is not None:
                                onlywhitespace = False
                        if onlywhitespace:
                            break
                elif isinstance(e, folia.AbstractTextMarkup):
                    e = e.copy()
                    length = len(e.text())

                if src and offsets and src is not prevsrc:
                    ancestors = list(src.ancestors(folia.AbstractStructureElement))
                    if len(ancestors) >= 2 and ancestors[1] is element:
                        if debug: print("Setting offset for text in  " + repr(ancestors[0]) + " to " + str(offset) + ", reference " + repr(element) ,file=sys.stderr)
                        src.offset = offset
                    elif forceoffsetref:
                        if debug: print("Setting offset with explicit reference for text in  " + repr(ancestors[0]) + " to " + str(offset) + ", reference " + repr(element) ,file=sys.stderr)
                        src.offset = offset
                        if element.id is None:
                            raise Exception("Unable to use element " + repr(element) + " as an explicit reference for offsets, because it has no ID. Consider processing the document with foliaid first to automatically assign IDs.")
                        src.ref = element.id
                    prevsrc = src

                newtextsequence.append(e)
                offset += length

        if newtextsequence:
            if debug: print("Setting text for " + repr(element) + ":" , newtextsequence, file=sys.stderr)
            return element.replace(folia.TextContent, *newtextsequence, cls=cls) #appends if new

def cleanredundancy(element, cls, debug=False):
    if element.hastext(cls, strict=True):
        try:
            mycontent = element.textcontent(cls)
        except folia.NoSuchText:
            return
        deepertexts = [ e for e in element.select(folia.TextContent, ignore=[True, folia.AbstractAnnotationLayer, folia.String, folia.Morpheme, folia.Phoneme, folia.Correction]) if e is not mycontent and e.cls == cls ]
        if deepertexts:
            #there is deeper text, remove text on this element
            if debug: print("Removing text for " + repr(element) + ":" , mycontent.text(), file=sys.stderr)
            element.remove(mycontent)

def processelement(element, settings):
    if not isinstance(element, folia.AbstractSpanAnnotation): #prevent infinite recursion
        for e in element:
            if isinstance(e, folia.AbstractElement):
                if settings.debug: print("Processing ", repr(e),file=sys.stderr)
                processelement(e,settings)
        if element.PRINTABLE:
            if any( isinstance(element,C) for C in settings.Classes):
                for cls in element.doc.textclasses:
                    if settings.cleanredundancy:
                        cleanredundancy(element, cls, settings.debug)
                    else:
                        settext(element, cls, settings.offsets, settings.forceoffsetref, settings.debug)

def addoffsets(element, textclass):
    """Compute text offsets in existing child elements"""
    if settings.forceoffsetref:
        raise NotImplementedError("Unable to compute offsets against a fixed reference")
    parent = element.parent
    try:
        elementtextcontent = element.textcontent(textclass)
    except folia.NoSuchText:
        print(f"No text for {element}",file=sys.stderr)
        return False
    try:
        parenttextcontent = parent.textcontent(textclass)
    except folia.NoSuchText:
        print(f"No text for parent of {element}",file=sys.stderr)
        return False
    if not hasattr(parent, 'addoffsetcursor'):
        parent.addoffsetcursor = 0
    startoffset = parent.addoffsetcursor
    elementtext = elementtextcontent.text().replace("\n", " ") #insensitive to newlines
    parenttext = parenttextcontent.text().replace("\n", " ")
    while parenttext[parent.addoffsetcursor:parent.addoffsetcursor+len(elementtext)] != elementtext:
        parent.addoffsetcursor += 1
        if parent.addoffsetcursor >= len(parenttext):
            raise folia.InconsistentText(f"Unable to find offset for {element} with text '{elementtext}' in parent text '{parenttext}', started at offset {startoffset}")
    elementtextcontent.offset = parent.addoffsetcursor
    if settings.debug:
        print(f"Assigning offset {parent.addoffsetcursor} to {element}",file=sys.stderr)
    parent.addoffsetcursor += len(elementtext)
    return True


def process(filename):
    print("Converting " + filename,file=sys.stderr)
    doc = folia.Document(file=filename, processor=folia.Processor.create(name="foliatextcontent", version=TOOLVERSION, src="https://github.com/proycon/foliatools") )

    if settings.linkstrings:
        for element in doc.select(folia.AbstractStructureElement):
            for cls in element.doc.textclasses:
                linkstrings(element, cls, settings.debug)

    if settings.Classes:
        for e in doc.data:
            processelement(e, settings)

    if settings.OffsetClasses:
        for Class in settings.OffsetClasses:
            for e in doc.select(Class):
                for cls in doc.textclasses:
                    addoffsets(e, cls)


    if settings.inplaceedit:
        doc.save()
    else:
        print(doc.xmlstring())

def processdir(d):
    print("Searching in  " + d, file=sys.stderr)
    for f in glob.glob(os.path.join(d ,'*')):
        if f[-len(settings.extension) - 1:] == '.' + settings.extension:
            process(f)
        elif settings.recurse and os.path.isdir(f):
            processdir(f)


class settings:
    Classes = [] #class to add text for
    inplaceedit = False
    offsets = True #add offsets when adding text?
    OffsetClasses = [] #classes to add offsets for
    forceoffsetref = False
    linkstrings = False

    cleanredundancy = False

    extension = 'xml'
    recurse = False
    encoding = 'utf-8'

    debug = False

    textclasses =[]


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "E:hsSpPdDtT:O:XMe:wT:Fc", ["help"])
    except getopt.GetoptError as err:
        print(str(err),file=sys.stderr)
        usage()
        sys.exit(2)



    for o, a in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        elif o == '-c':
            settings.cleanredundancy = True
            settings.Classes.append(folia.AbstractStructureElement)
        elif o == '-d':
            settings.Classes.append(folia.Division)
        elif o == '-t':
            settings.Classes.append(folia.Text)
        elif o == '-s':
            settings.Classes.append(folia.Sentence)
        elif o == '-p':
            settings.Classes.append(folia.Paragraph)
        elif o == '-T':
            settings.Classes += [ folia.XML2CLASS[tag] for tag in a.split(',') if tag ]
        elif o == '-O':
            settings.OffsetClasses += [ folia.XML2CLASS[tag] for tag in a.split(',') if tag ]
        elif o == '-X':
            settings.offsets = False
        elif o == '-e':
            settings.encoding = a
        elif o == '-E':
            settings.extension = a
        elif o == '-F':
            settings.forceoffsetref = True
        elif o == '-M':
            settings.linkstrings = True
        elif o == '-w':
            settings.inplaceedit = True
        elif o == '-r':
            settings.recurse = True
        elif o == '-D':
            print("Debug enabled",file=sys.stderr)
            settings.debug = True
        else:
            raise Exception("No such option: " + o)



    if len(settings.Classes) > 1 or len(settings.OffsetClasses) > 1:
        settings.forceoffsetref = False

    if args:
        for x in args:
            if os.path.isdir(x):
                processdir(x)
            elif os.path.isfile(x):
                process(x)
            else:
                print("ERROR: File or directory not found: " + x,file=sys.stderr)
                sys.exit(3)
    else:
        print("ERROR: Nothing to do, specify one or more files or directories",file=sys.stderr)

if __name__ == "__main__":
    main()

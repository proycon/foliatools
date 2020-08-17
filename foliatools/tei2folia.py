#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#---------------------------------------------------------------
# TEI to FoLiA Converter
#   by Maarten van Gompel
#   Centre for Language Studies
#   Radboud University Nijmegen
#   proycon AT anaproy DOT nl
#
#   Licensed under GPLv3
#----------------------------------------------------------------

"""Converts SOME VARIANTS of TEI to FoLiA XML. Because of the great diversity in TEI formats, it is not guaranteed to work in all circumstances."""

import sys
import argparse
import os.path
import lxml.etree
import traceback
import time
from socket import getfqdn
from datetime import datetime
from urllib.parse import  urlparse
from urllib.request import urlretrieve
import folia.main as folia
from foliatools import VERSION as TOOLVERSION
from foliatools.foliaid import assignids

class CustomResolver(lxml.etree.Resolver):
    #adapted from http://www.hoboes.com/Mimsy/hacks/caching-dtds-using-lxml-and-etree/
    def __init__(self, dtddir):
        self.dtddir = dtddir
        super().__init__()

    def resolve(self, url, id, context):
        #determine cache path
        filename = os.path.basename(url)
        dtdfile = os.path.join(self.dtddir, filename)
        print("(obtaining dtd for", url, " in ", self.dtddir, ")",file=sys.stderr)
        if not os.path.exists(self.dtddir):
            os.makedirs(self.dtddir)
        #cache if necessary
        if not os.path.exists(dtdfile):
            lockfile = os.path.join(self.dtddir,".tei2folia.lock") #implementing a locking mechanism in case of concurrency
            waited = 0
            while os.path.exists(lockfile):
                print("(waiting for lock file to go away)", file=sys.stderr)
                waited += 1
                time.sleep(1)
                if waited > 60:
                    print("ERROR: Unable to get a lock for obtaining DTD files",file=sys.stderr)
                    sys.exit(2)
            with open(lockfile,'w', encoding='utf-8') as f:
                print(url, file=f)
            filename, headers = urlretrieve(url, dtdfile)
            os.unlink(lockfile)
        #resolve the cached file
        return self.resolve_file(open(dtdfile), context, base_url=url)


def convert(filename, transformer, parser=None, **kwargs):
    if not os.path.exists(filename):
        raise Exception("File not found: " + filename)
    begindatetime = datetime.now()
    if parser is None:
        parser = lxml.etree.XMLParser(load_dtd=True)
        parser.resolvers.add( CustomResolver(kwargs.get('dtddir','.')) )
    if 'forcenamespace' in kwargs and kwargs['forcenamespace']:
        with open(filename,'rb') as f:
            data = f.read()
        if data.find(b"xmlns=\"http://www.tei-c.org/ns/1.0\"") == -1:
            data = data.replace(b"<TEI ",b"<TEI xmlns=\"http://www.tei-c.org/ns/1.0\" ")
            data = data.replace(b"<TEI.2 ",b"<TEI.2 xmlns=\"http://www.tei-c.org/ns/1.0\" ")
        parsedsource = lxml.etree.fromstring(data, parser)
        del data
    else:
        with open(filename,'rb') as f:
            parsedsource = lxml.etree.parse(f, parser)
    transformed = transformer(parsedsource,quiet="true")
    try:
        doc = folia.Document(tree=transformed, debug=kwargs.get('debug',0))
    except folia.DeepValidationError as e:
        print("DEEP VALIDATION ERROR on full parse by library in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        return False
    except Exception as e:
        print("VALIDATION ERROR on full parse by library in " + filename,file=sys.stderr)
        print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
        if kwargs.get('traceback') or kwargs.get('debug'):
            print("-- Full traceback follows -->",file=sys.stderr)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_exception(ex_type, ex, tb)
        return False
    if doc.textvalidationerrors:
        print("VALIDATION ERROR because of text validation errors, in " + filename,file=sys.stderr)
        return False
    #augment the processor added by the above XSL stylesheet
    doc.provenance.processors[-1].version = TOOLVERSION
    doc.provenance.processors[-1].host = getfqdn()
    try:
        executable = os.path.basename(sys.argv[0])
        doc.provenance.processors[-1].command = " ".join([executable] + sys.argv[1:])
    except:
        pass
    doc.provenance.processors[-1].begindatetime = begindatetime
    doc.provenance.processors[-1].enddatetime = datetime.now()
    doc.provenance.processors[-1].folia_version = folia.FOLIAVERSION
    if 'USER' in os.environ:
        doc.provenance.processors[-1].user = os.environ['USER']
    #add subprocessor for validation
    doc.provenance.processors[-1].append( folia.Processor.create(name="foliavalidator", version=TOOLVERSION, src="https://github.com/proycon/foliatools", metadata={"valid": "yes"}) )
    if not kwargs.get('quiet'):
        postprocess_warnings(doc)
    if not kwargs.get('leaveparts'):
        postprocess_tempparts(doc)
    if not kwargs.get('leavenotes'):
        postprocess_notes(doc)
    if kwargs.get('ids'):
        assignids(doc)
        doc.provenance.processors[-1].append( folia.Processor.create(name="foliaid", version=TOOLVERSION, src="https://github.com/proycon/foliatools") )

    return doc



def mergeparts(sequence):
    """Merges a sequence of temporary parts, following the assumption that each only has one textcontent element which will be concatenated with the others"""
    try:
        sequence[0].ancestor(folia.Paragraph, folia.Sentence, folia.Part)
        Mergedclass = folia.Part
    except folia.NoSuchAnnotation:
        Mergedclass = folia.Paragraph

    parent = sequence[0].parent

    index = parent.getindex(sequence[0])
    newtextcontent = []
    for part in sequence:
        try:
            parent.remove(part)
        except ValueError:
            print("WARNING: Unable to remove part " + repr(part) + " from parent " + repr(parent) + " as it does not exist",file=sys.stderr)
        if isinstance(part, folia.Part):
            try:
                newtextcontent += part.textcontent().data
            except folia.NoSuchText:
                #ok, no biggie
                pass
        else: #intermediate elements (linebreaks and such), add as-is
            newtextcontent.append(part)

    if isinstance(parent, (folia.Table, folia.List)):
        print("WARNING: Unable to merge parts in table/list root. Deleting parts!",file=sys.stderr)
        parent.insert(index, folia.Comment, value="[tei2folia WARNING] Unable to merge parts in this context. Deleted " + str(len(sequence)) + " parts with text: " + " ".join(str(t) for t in newtextcontent))
        return None

    mergedelement = parent.insert(index, Mergedclass, cls="aggregated")
    newtextcontent = mergedelement.append(folia.TextContent, *newtextcontent)
    return mergedelement


def insequence(prevpart, nextpart):
    """Determines if two parts are in sequence and if there are any intermediate structures which may be subsumed (like linebreaks and comments)"""
    sequence = [] #intermediate sequence
    result = False
    e = prevpart
    while True:
        e = e.next((folia.Part, folia.Linebreak, folia.Comment))
        if e is nextpart:
            return True, sequence
        elif e is None:
            return False, []
        elif e is not prevpart:
            sequence.append(e)




def postprocess_tempparts(doc):
    """Resolve temporary parts"""
    sequences = []
    buffer = []
    for part in doc.select(folia.Part, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/parts.foliaset.ttl"):
        if part.cls[:4] == "temp":
            if buffer:
                isinsequence, intermediatesequence = insequence(buffer[-1], part)
                buffer += intermediatesequence #add stuff in between (linebreaks, comments, notes) which we can subsume
            else:
                isinsequence = True #new sequence

            if not isinsequence and buffer:
                #process the buffer
                sequences.append(buffer)
                buffer = [part] #new buffer
            else:
                if isinsequence:
                    buffer.append(part)
                else:
                    buffer = []

    if buffer:
        sequences.append(buffer)

    for sequence in sequences:
        mergeparts(sequence)

def postprocess_notes(doc):
    for i, noteref in enumerate(doc.select(folia.TextMarkupReference, "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/tei2folia/references.foliaset.ttl")):
        if noteref.cls and (noteref.cls == "footnote" or noteref.cls[:4] == "note"):
            #we treat all notes as footnotes and move them to the end of the parent division, with a proper reference in place
            div = noteref.ancestor(folia.Division) #these will hold the footnotes
            if div.hastext(strict=True):
                #this won't do, go one level higher
                div = div.ancestor(folia.Division) #these will hold the footnotes
            note_id = noteref.doc.id+".note."+str(i)
            #add the note
            try:
                if noteref.data and noteref.text().strip():
                    div.append(folia.Note, folia.TextContent(doc,*noteref.data), id=note_id, cls=noteref.cls if noteref.cls else "unspecified")
                else:
                    raise folia.NoSuchText
            except folia.NoSuchText:
                div.append(folia.Note, id=note_id, cls=noteref.cls if noteref.cls else "unspecified")
            noteref.data = [] #clear data
            noteref.type = "note"
            noteref.idref = note_id

def postprocess_warnings(doc):
    for comment in doc.select(folia.Comment):
        if comment.value.find("tei2folia") != -1:
            print(comment.value, file=sys.stderr)

def loadxslt():
    xsltfilename = "tei2folia.xsl"
    xsldir = os.path.dirname(__file__)
    if xsltfilename[0] != '/': xsltfilename = os.path.join(xsldir, xsltfilename)
    if not os.path.exists(xsltfilename):
        raise Exception("XSL Stylesheet not found: " + xsltfilename)
    xslt = lxml.etree.parse(xsltfilename)
    transformer = lxml.etree.XSLT(xslt)
    return transformer


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory, set to - for stdout", action="store",default=".",required=False)
    parser.add_argument('--dtddir',type=str, help="Directory where DTDs are stored (tei2folia will actively try to obtain the DTDs)", action="store",default=".",required=False)
    parser.add_argument('-D','--debug',type=int,help="Debug level", action='store',default=0)
    parser.add_argument('-q','--quiet',help="Do not output warnings", action='store_true',default=False)
    parser.add_argument('-b','--traceback',help="Provide a full traceback on validation errors", action='store_true', default=False)
    parser.add_argument('-P','--leaveparts',help="Do *NOT* resolve temporary parts", action='store_true', default=False)
    parser.add_argument('-N','--leavenotes',help="Do *NOT* resolve inline notes (t-gap)", action='store_true', default=False)
    parser.add_argument('-i','--ids',help="Generate IDs for all structural elements", action='store_true', default=False)
    parser.add_argument('-f','--forcenamespace',help="Force a TEI namespace even if the input document has none", action='store_true', default=False)
    parser.add_argument('files', nargs='+', help='TEI Files to process')
    args = parser.parse_args()
    print("Instantiating XML parser",file=sys.stderr)
    xmlparser = lxml.etree.XMLParser(load_dtd=True,no_network=False)
    xmlparser.resolvers.add( CustomResolver(args.dtddir) )
    for filename in args.files:
        print("Converting", filename,file=sys.stderr)
        doc = convert(filename, loadxslt(), xmlparser, **args.__dict__)
        if doc is False:
            print("Unable to convert ", filename,file=sys.stderr)
            sys.exit(1) #an error occured
        try:
            if args.outputdir == "-":
                print(doc.xmlstring())
            else:
                filename = os.path.basename(filename)
                if filename[-4:] == '.xml':
                    filename = filename[:-4] + '.folia.xml'
                else:
                    filename += '.folia.xml'
                print("   Writing", filename,file=sys.stderr)
                doc.save(os.path.join(args.outputdir, filename))
        except Exception as e:
            print("SERIALISATION ERROR for " + filename + ". This should not happen.",file=sys.stderr)
            print(e.__class__.__name__ + ": " + str(e),file=sys.stderr)
            print("-- Full traceback follows -->",file=sys.stderr)
            ex_type, ex, tb = sys.exc_info()
            traceback.print_exception(ex_type, ex, tb)
            print("Unable to convert ", filename,file=sys.stderr)
            sys.exit(1) #an error occured
    sys.exit(0)


if __name__ == '__main__':
    main()


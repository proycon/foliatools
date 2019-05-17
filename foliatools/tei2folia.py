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
#
# This script converts *SOME VARIANTS* of TEI to the FoLiA format.
# Because of the great diversity in TEI formats, it is not
# guaranteed to work in all circumstances.
#
#----------------------------------------------------------------

import sys
import argparse
import os.path
import lxml.etree
import traceback
from socket import getfqdn
from datetime import datetime
from foliatools import VERSION as TOOLVERSION
from urllib.parse import  urlparse
from urllib.request import urlretrieve
import folia.main as folia
import foliatools.xslt as xslt

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
            filename, headers = urlretrieve(url, dtdfile)
        #resolve the cached file
        return self.resolve_file(open(dtdfile), context, base_url=url)


def convert(filename, transformer, parser=None, **kwargs):
    if not os.path.exists(filename):
        raise Exception("File not found: " + filename)
    begindatetime = datetime.now()
    if parser is None:
        parser = lxml.etree.XMLParser(load_dtd=True)
        parser.resolvers.add( CustomResolver(kwargs.get('dtddir','.')) )
    with open(filename,'rb') as f:
        parsedsource = lxml.etree.parse(f, parser)
    transformed = transformer(parsedsource)
    try:
        doc = folia.Document(tree=transformed)
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
    return doc


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
    parser = argparse.ArgumentParser(description="Convert *SOME VARIANTS* of TEI to FoLiA XML. Because of the great diversity in TEI formats, it is not guaranteed to work in all circumstances.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory, set to - for stdout", action="store",default=".",required=False)
    parser.add_argument('--dtddir',type=str, help="Directory where DTDs are stored (tei2folia will actively try to obtain the DTDs)", action="store",default=".",required=False)
    parser.add_argument('-D','--debug',type=int,help="Debug level", action='store',default=0)
    parser.add_argument('-b','--traceback',help="Provide a full traceback on validation errors", action='store_true', default=False)
    parser.add_argument('files', nargs='+', help='TEI Files to process')
    args = parser.parse_args()
    print("Instantiating XML parser",file=sys.stderr)
    xmlparser = lxml.etree.XMLParser(load_dtd=True,no_network=False)
    xmlparser.resolvers.add( CustomResolver(args.dtddir) )
    for filename in args.files:
        print("Converting", filename,file=sys.stderr)
        doc = convert(filename, loadxslt(), xmlparser, **args.__dict__)
        if doc is False: return False #an error occured
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
            return False




if __name__ == '__main__':
    main()


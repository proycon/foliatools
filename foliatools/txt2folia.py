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

"""Converts plain text to FoLiA XML."""

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


def convert(filename, **kwargs):
    if not os.path.exists(filename):
        raise Exception("File not found: " + filename)

    if 'id' in kwargs:
        docid = folia.makencname(kwargs['id'])
    else:
        docid = folia.makencname(os.path.basename(filename).split('.')[0])
    doc = folia.Document(id=docid, processor=folia.Processor.create(name="txt2folia", version=TOOLVERSION) )
    body = doc.append(folia.Text(doc, id=docid + '.text'))
    buffer = []
    with open(filename,'r',encoding=kwargs['encoding']) as f:
        for line in f:
            if kwargs.get('sentenceperline'):
                body.append(folia.Sentence, line.strip())
            elif kwargs.get('paragraphperline'):
                body.append(folia.Paragraph, line.strip())
            elif kwargs.get('nostructure'):
                if kwargs.get('linebreaks'):
                    buffer.append( line.strip() )
                    buffer.append(folia.LineBreak(doc))
                else:
                    if buffer and buffer[-1][-1] not in (' ','-'):
                        buffer.append( " " + line.strip() )
                    else:
                        buffer.append( line.strip() )
            else:
                if not line.strip():
                    #empty line, add buffer
                    body.append(folia.Paragraph, *buffer)
                    buffer = []
                else:
                    buffer.append(line)
                    if kwargs.get('linebreaks'):
                        buffer.append(folia.LineBreak(doc))

    if buffer:
        if kwargs.get('nostructure'):
            body.settext(folia.TextContent(doc, *buffer ))
        else:
            body.append(folia.Paragraph, *buffer)

    return doc

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory, set to - for stdout", action="store",default=".",required=False)
    parser.add_argument('--id',type=str,help="Document ID", action='store')
    parser.add_argument('--encoding',type=str,help="Encoding", action='store',default='utf-8')
    parser.add_argument('--sentenceperline',help="Assume one sentence per line", action='store_true')
    parser.add_argument('--paragraphperline',help="Assume one paragraph per line", action='store_true')
    parser.add_argument('--paragraphs',help="Assumes paragraphs seperated by an empty line (this is the default)", action='store_true')
    parser.add_argument('--nostructure',help="Do not extract any structure, just wrap the entire text in a minimal FoLiA structure", action='store_true')
    parser.add_argument('--linebreaks',help="Explicitly encode linebreaks", action='store_true')
    parser.add_argument('files', nargs='+', help='Text files to process')
    args = parser.parse_args()

    for filename in args.files:
        print("Converting", filename,file=sys.stderr)
        doc = convert(filename, **args.__dict__)
        if doc is False:
            print("Unable to convert ", filename,file=sys.stderr)
            sys.exit(1) #an error occured
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
    sys.exit(0)

if __name__ == '__main__':
    main()


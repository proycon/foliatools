#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#---------------------------------------------------------------
# Transcribed Speech to FoLiA Converter
#   by Maarten van Gompel
#   KNAW Humanities Cluster
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

def splittime(ms):
    s = int(ms / 1000)
    ms = ms % 1000
    min = int(s / 60)
    s = s % 60
    h = int(min / 60)
    min = min % 24
    return f"{h}:{min}:{s}.{ms}"

def convert(filename, **kwargs):
    if not os.path.exists(filename):
        raise Exception("File not found: " + filename)

    if 'id' in kwargs and kwargs['id']:
        docid = folia.makencname(kwargs['id'])
    else:
        docid = folia.makencname(os.path.basename(filename).split('.')[0])
    doc = folia.Document(id=docid, processor=folia.Processor.create(name="transcribedspeech2folia", version=TOOLVERSION) )
    body = doc.append(folia.Text(doc, id=docid + '.text'))
    event = body.append(folia.Event(doc, cls="conversation", id=docid + '.conversation'))
    lines = []
    speaker = None
    text = None
    starttime = None
    endtime = None
    with open(filename,'r',encoding=kwargs['encoding']) as f:
        lines = [ x.strip() for x in f.readlines() ]

    skip = 0
    for i, line in enumerate(lines):
        if skip > 0:
            skip -= 1 
            continue
        if line.startswith('[StartTime:') and line.endswith('ms]'):
            starttime = splittime(int(line[12:-3]))
            if not event.begintime:
                event.begintime = folia.parsetime(starttime)
        elif line.startswith('[EndTime:') and line.endswith('ms]'):
            #check if this is a real end and if the same speaker doesn't simply continue in the next 'event' 
            speaker_continues = i + 2 < len(lines) and lines[i+1].startswith('[StartTime:') and lines[i+2].startswith(f"[Speaker: {speaker}]")

            if not speaker_continues:
                endtime = splittime(int(line[10:-3]))
                #finish the event
                if speaker and text:
                    if starttime:
                        event.append(folia.Utterance(doc, text=text, speaker=speaker, endtime=endtime, begintime=starttime))
                    else:
                        event.append(folia.Utterance(doc, text=text, speaker=speaker, endtime=endtime))
                    starttime = None
                text = None
            else:
                if not starttime:
                    starttime = splittime(int(lines[i+1][12:-3]))
                skip = 2
        elif line.startswith('[Speaker:') and line.endswith(']'):
            if speaker and text:
                #speaker changed
                if starttime:
                    event.append(folia.Utterance(doc, text=text, speaker=speaker, begintime=starttime))
                else:
                    event.append(folia.Utterance(doc, text=text, speaker=speaker))
                starttime = None
            speaker = line[10:-1].strip()
            text = None
        else:
            if text: 
                text += " " + line.strip()
            else:
                text = line.strip()

    if endtime:
        event.endtime = folia.parsetime(endtime)

    return doc

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o','--outputdir',type=str, help="Output directory, set to - for stdout", action="store",default=".",required=False)
    parser.add_argument('--id',type=str,help="Document ID", action='store')
    parser.add_argument('--encoding',type=str,help="Encoding", action='store',default='utf-8')
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
            if filename[-4:] in ('.xml','.txt'):
                filename = filename[:-4] + '.folia.xml'
            else:
                filename += '.folia.xml'
            print("   Writing", filename,file=sys.stderr)
            doc.save(os.path.join(args.outputdir, filename))
    sys.exit(0)

if __name__ == '__main__':
    main()


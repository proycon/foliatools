# -*- coding: utf8 -*-

import lxml.etree
import sys
import glob
import getopt
import os.path
import io

def transform(xsltfilename, sourcefilename, targetfilename = None, encoding = 'utf-8', **kwargs):
    xsldir = os.path.dirname(__file__)
    if xsltfilename[0] != '/': xsltfilename = os.path.join(xsldir, xsltfilename)
    if not os.path.exists(xsltfilename):
        raise Exception("XSL Stylesheet not found: " + xsltfilename)
    elif not os.path.exists(sourcefilename):
        raise Exception("File not found: " + sourcefilename)
    xslt = lxml.etree.parse(xsltfilename)
    transformer = lxml.etree.XSLT(xslt)
    parsedsource = lxml.etree.parse(sourcefilename)
    kwargs = { k: lxml.etree.XSLT.strparam(v)  for k,v in kwargs.items() }
    transformed = transformer(parsedsource, **kwargs)
    if targetfilename:
        print("Wrote " + targetfilename,file=sys.stderr)
        f = io.open(targetfilename, 'w',encoding='utf-8')
        f.write(str(lxml.etree.tostring(transformed, pretty_print=False, encoding=encoding),encoding))
        f.close()
    else:
        print(str(lxml.etree.tostring(transformed, pretty_print=False, encoding=encoding),encoding))


def usage():
    print(settings.usage,file=sys.stderr)
    print("",file=sys.stderr)
    print("Parameters for output:"        ,file=sys.stderr)
    print("  -e [encoding]                Output encoding (default: utf-8)" ,file=sys.stderr)
    print("Parameters for processing directories:",file=sys.stderr)
    print("  -r                           Process recursively",file=sys.stderr)
    print("  -E [extension]               Set extension (default: xml)",file=sys.stderr)
    print("  -q                           Ignore errors",file=sys.stderr)
    print("  -s [url]                     Associate a CSS Stylesheet (URL, may be relative)",file=sys.stderr)
    print("  -T                           Retain tokenisation",file=sys.stderr)
    print("  -t [textclass]               Text class to output",file=sys.stderr)



class settings:
    autooutput = False
    extension = 'xml'
    recurse = False
    ignoreerrors = False
    encoding = 'utf-8'
    xsltfilename = "undefined.xsl"
    outputextension = 'UNDEFINED'
    usage = "UNDEFINED"
    css = ""
    textclass = "current"

def processdir(d):
    print("Searching in  " + d, file=sys.stderr)
    for f in glob.glob(os.path.join(d,'*')):
        if f[-len(settings.extension) - 1:] == '.' + settings.extension and f[-len(settings.outputextension) - 1:] != '.' + settings.outputextension:
            process(f)
        elif settings.recurse and os.path.isdir(f):
            processdir(f)

def process(inputfilename):
    try:
        kwargs = {}
        if settings.css:
            kwargs['css'] = settings.css
        if settings.textclass:
            kwargs['textclass'] = settings.textclass
        transform(settings.xsltfilename, inputfilename, None, settings.encoding, **kwargs)
    except Exception as e:
        if settings.ignoreerrors:
            print("ERROR: An exception was raised whilst processing " + inputfilename + ":", e, file=sys.stderr)
        else:
            raise e


def main(xsltfilename, outputextension, usagetext):
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:E:hrqs:Tt:", ["help"])
    except getopt.GetoptError as err:
        print(str(err), file=sys.stderr)
        usage()
        sys.exit(2)

    settings.xsltfilename = xsltfilename
    settings.outputextension = outputextension
    settings.usage = usagetext


    for o, a in opts:
        if o == '-h' or o == '--help':
            usage()
            sys.exit(0)
        elif o == '-T':
            settings.retaintokenisation = True
        elif o == '-e':
            settings.encoding = a
        elif o == '-E':
            settings.extension = a
        elif o == '-r':
            settings.recurse = True
        elif o == '-q':
            settings.ignoreerrors = True
        elif o == '-s':
            settings.css = a
        elif o == '-t':
            settings.textclass = a
        else:
            raise Exception("No such option: " + o)

    if args:
        for x in args:
            if os.path.isdir(x):
                processdir(x)
            elif os.path.isfile(x):
                process(x)
            else:
                print("ERROR: File or directory not found: " + x, file=sys.stderr)
                sys.exit(3)
    else:
        print("ERROR: Nothing to do, specify one or more files or directories",file=sys.stderr)

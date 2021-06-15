#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""
This convertor reads a FoLiA XML document and produces a
simple columned output format (supports CSV,TSV) in which each token appears on one
line. Note that only simple token annotations are supported and a lot
of FoLiA data can not be intuitively expressed in a simple columned format!
"""

from __future__ import print_function, unicode_literals, division, absolute_import

import getopt
import io
import sys
import os
import glob
import folia.main as folia

def usage():
    print("folia2columns", file=sys.stderr)
    print("  by Maarten van Gompel (proycon)", file=sys.stderr)
    print("  Centre for Language and Speech Technology, Radboud University Nijmegen",file=sys.stderr)
    print("  2016-2019 - Licensed under GPLv3", file=sys.stderr)
    print("", file=sys.stderr)
    print(__doc__, file=sys.stderr)
    print("", file=sys.stderr)
    print("Usage: folia2columns [options] -C [columns] file-or-dir1 file-or-dir2 ..etc..", file=sys.stderr)

    print("Parameters:", file=sys.stderr)
    print("  -c [columns]                 Comma separated list of desired column layout (mandatory), choose from:", file=sys.stderr)
    print("                               id      - output word ID", file=sys.stderr)
    print("                               text    - output the text of the word (the word itself)", file=sys.stderr)
    print("                               pos     - output PoS annotation class", file=sys.stderr)
    print("                               poshead - output PoS annotation head feature", file=sys.stderr)
    print("                               lemma   - output lemma annotation class", file=sys.stderr)
    print("                               sense   - output sense annotation class", file=sys.stderr)
    print("                               phon    - output phonetic annotation class", file=sys.stderr)
    print("                               senid   - output sentence ID", file=sys.stderr)
    print("                               parid   - output paragraph ID", file=sys.stderr)
    print("                               N     - word/token number (absolute)", file=sys.stderr)
    print("                               n     - word/token number (relative to sentence)", file=sys.stderr)
    print("  -u [units]                   Desired token unit, choose from:", file=sys.stderr)
    print("                               word      - output words (default)", file=sys.stderr)
    print("                               sentence  - output sentences", file=sys.stderr)
    print("                               paragraph - output paragraphs", file=sys.stderr)
    print("Options:", file=sys.stderr)
    print("  --csv                        Output in CSV format", file=sys.stderr)
    print("  -o [filename]                Output to a single output file instead of stdout", file=sys.stderr)
    print("  -O                           Output each file to similarly named file (.columns or .csv)", file=sys.stderr)
    print("  -e [encoding]                Output encoding (default: utf-8)", file=sys.stderr)
    print("  -H                           Suppress header output", file=sys.stderr)
    print("  -S                           Suppress sentence spacing  (no whitespace between sentences)", file=sys.stderr)
    print("  -x [sizeinchars]             Space columns for human readability (instead of plain tab-separated columns)", file=sys.stderr)
    print("  -t                           Output tokenized rather than untokenized paragraphs/sentences when -u sentence or -u paragraph is used", file=sys.stderr)
    print("Parameters for processing directories:", file=sys.stderr)
    print("  -r                           Process recursively", file=sys.stderr)
    print("  -E [extension]               Set extension (default: xml)", file=sys.stderr)
    print("  -O                           Output each file to similarly named .txt file", file=sys.stderr)
    print("  -P                           Like -O, but outputs to current working directory", file=sys.stderr)
    print("  -q                           Ignore errors", file=sys.stderr)

class settings:
    output_header = True
    csv = False
    outputfile = None
    sentencespacing = True
    ignoreerrors = False
    nicespacing = 0
    autooutput = False
    extension = 'xml'
    recurse = False
    encoding = 'utf-8'
    columnconf = []
    unit = "word"
    tok = False

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "o:OPhHSc:x:E:rqu:t", ["help", "csv"])
    except getopt.GetoptError as err:
        print(str(err), file=sys.stderr)
        usage()
        sys.exit(2)

    outputfile = None

    for o, a in opts:
        if o == '-c':
            for a in a.split(','):
                settings.columnconf.append(a)
        elif o == '-h':
            usage()
            sys.exit(0)
        elif o == '-u':
            if a in ['word','sentence','paragraph']:
                settings.unit = a
            else:
                print("ERROR: Unknown unit (-u) type specified: choose from word, sentence, paragraph", file=sys.stderr)
                usage()
                sys.exit(2)
        elif o == '-H':
            settings.output_header = False
        elif o == '-S':
            settings.sentencespacing = False
        elif o == '-e':
            settings.encoding = a
        elif o == '-o':
            outputfile = a
        elif o == '-O':
            settings.autooutput = True
        elif o == '-P':
            settings.autooutput = True
            settings.autooutput_cwd = True
        elif o == '-x':
            settings.nicespacing = int(a)
        elif o == '-t':
            settings.tok = True
        elif o == '-E':
            settings.extension = a
        elif o == '-r':
            settings.recurse = True
        elif o == '-q':
            settings.ignoreerrors = True
        elif o == '--csv':
            settings.csv = True
        else:
            raise Exception("No such option: " + o)

    if not settings.columnconf:
        print("ERROR: No column configuration specified (use -c)", file=sys.stderr)
        usage()
        sys.exit(2)


    if args:
        if outputfile: outputfile = io.open(outputfile,'w',encoding=settings.encoding)
        for x in args:
            if os.path.isdir(x):
                processdir(x,outputfile)
            elif os.path.isfile(x):
                process(x, outputfile)
            else:
                print("ERROR: File or directory not found: " + x, file=sys.stderr)
                sys.exit(3)
        if outputfile: outputfile.close()
    else:
        print ("ERROR: Nothing to do, specify one or more files or directories", file=sys.stderr)



def resize(s, i, spacing):
    if len(s) >= spacing[i]:
        s = s[0:spacing[i] - 1] + ' '
    elif len(s) < spacing[i]:
        s = s + (' ' * (spacing[i] - len(s)))
    #print '[' + s + ']', len(s), spacing[i]
    return s

def processdir(d, outputfile = None, i = 0):
    print("Searching in  " + d, file=sys.stderr)
    for f in glob.glob(os.path.join(d, '*')):
        if f[-len(settings.extension) - 1:] == '.' + settings.extension:
            process(f, outputfile, i)
            i = i + 1
        elif settings.recurse and os.path.isdir(f):
            i = processdir(f, outputfile, i)

def process(filename, outputfile=None, filesProcessed=0):
    try:
        print("Processing " + filename, file=sys.stderr)
        doc = folia.Document(file=filename)
        prevsen = None

        if settings.autooutput:
            if settings.csv:
                ext = '.csv'
            else:
                ext = '.columns'
            if filename[-len(settings.extension) - 1:].lower() == '.' +settings.extension:
                outfilename = filename[:-len(settings.extension) - 1] + ext
            else:
                outfilename += ext
            if settings.autooutput_cwd:
                outfilename = os.path.basename(outfilename)

            print(" Saving as " + outfilename, file=sys.stderr)
            outputfile = io.open(outfilename,'w',encoding=settings.encoding)


        if settings.nicespacing:
            spacing = []
            for c in settings.columnconf:
                if c == 'n':
                    spacing.append(3)
                elif c == 'N':
                    spacing.append(7)
                elif c == 'poshead':
                    spacing.append(5)
                else:
                    spacing.append(settings.nicespacing)

        if settings.output_header and not(outputfile and filesProcessed > 0): #avoid continuously reprinting header when printing multiple files to single file

            if settings.csv:
                columns = [ '"' + x.upper()  + '"' for x in settings.columnconf ]
            else:
                columns = [ x.upper()  for x in settings.columnconf ]

            if settings.nicespacing and not settings.csv:
                columns = [ resize(x, i, spacing) for i, x in enumerate(settings.columnconf) ]

            if settings.csv:
                line = ','.join(columns)
            else:
                line = '\t'.join(columns)

            if outputfile:
                outputfile.write(line)
                outputfile.write('\n')
            else:
                if sys.version < '3':
                    print(line.encode(settings.encoding))
                else:
                    print(line)

        wordnum = 0

        def getunitfromdoc():
            if settings.unit == "word":
                return doc.words()
            elif settings.unit == "sentence":
                return doc.sentences()
            elif settings.unit == "paragraph":
                return doc.paragraphs()
            else:
                return doc.words()

        for i, w in enumerate(getunitfromdoc()):
            if settings.unit == "word":
                if w.sentence() != prevsen and i > 0:
                    if settings.sentencespacing:
                        if outputfile:
                            outputfile.write('\n')
                        else:
                            print()
                    wordnum = 0
                prevsen = w.sentence()
                wordnum += 1
            columns = []
            for c in settings.columnconf:
                if c == 'id':
                    columns.append(w.id)
                elif c == 'text':
                    if settings.unit == "word":
                        columns.append(w.text())
                    else:
                        if settings.tok:
                            wordspar = []
                            for j, word in enumerate(w.words()):
                                wordspar.append(word.text())
                            if wordspar:
                                columns.append(' '.join(wordspar))
                        else:
                            columns.append(w.text())
                elif c == 'n':
                    columns.append(str(wordnum))
                elif c == 'N':
                    columns.append(str(i+1))
                elif c == 'pos':
                    if settings.unit == "paragraph" or settings.unit == "sentence":
                        pospar = []
                        for j, word in enumerate(w.words()):
                            try:
                                pospar.append(word.annotation(folia.LemmaAnnotation).cls)
                            except:
                                pass
                        if pospar:
                            columns.append(' '.join(pospar))
                        else:
                            columns.append('-')
                    else:
                        try:
                            columns.append(w.annotation(folia.PosAnnotation).cls)
                        except:
                            columns.append('-')
                elif c == 'poshead':
                    if settings.unit == "paragraph" or settings.unit == "sentence":
                        posheadpar = []
                        for j, word in enumerate(w.words()):
                            try:
                                posheadpar.append(word.annotation(folia.LemmaAnnotation).cls)
                            except:
                                pass
                        if posheadpar:
                            columns.append(' '.join(posheadpar))
                        else:
                            columns.append('-')
                    else:
                        try:
                            columns.append(w.annotation(folia.PosAnnotation).feat('head'))
                        except:
                            columns.append('-')
                elif c == 'lemma':
                    if settings.unit == "paragraph" or settings.unit == "sentence":
                        lemmapar = []
                        for j, word in enumerate(w.words()):
                            try:
                                lemmapar.append(word.annotation(folia.LemmaAnnotation).cls)
                            except:
                                pass
                        if lemmapar:
                            columns.append(' '.join(lemmapar))
                        else:
                            columns.append('-')
                        
                    else:
                        try:
                            columns.append(w.annotation(folia.LemmaAnnotation).cls)
                        except:
                            columns.append('-')
                elif c == 'sense':
                    if settings.unit == "paragraph" or settings.unit == "sentence":
                        sensepar = []
                        for j, word in enumerate(w.words()):
                            try:
                                sensepar.append(word.annotation(folia.LemmaAnnotation).cls)
                            except:
                                pass
                        if sensepar:
                            columns.append(' '.join(sensepar))
                        else:
                            columns.append('-')
                    else:
                        try:
                            columns.append(w.annotation(folia.SenseAnnotation).cls)
                        except:
                            columns.append('-')
                elif c == 'phon':
                    if settings.unit == "paragraph" or settings.unit == "sentence":
                        phonpar = []
                        for j, word in enumerate(w.words()):
                            try:
                                phonpar.append(word.annotation(folia.LemmaAnnotation).cls)
                            except:
                                pass
                        if phonpar:
                            columns.append(' '.join(phonpar))
                        else:
                            columns.append('-')
                    else:
                        try:
                            columns.append(w.annotation(folia.PhonAnnotation).cls)
                        except:
                            columns.append('-')
                elif c == 'senid' and settings.unit == "word":
                    columns.append(w.sentence().id)
                elif c == 'parid' and (settings.unit == "word" or settings.unit == "sentence"):
                    try:
                        columns.append(w.paragraph().id)
                    except:
                        columns.append('-')
                elif c:
                    print("ERROR: Unsupported configuration: " + c, file=sys.stderr)
                    sys.exit(1)

            if settings.nicespacing and not settings.csv:
                columns = [ resize(x,j, spacing) for j,x  in enumerate(columns) ]

            if settings.csv:
                line = ",".join([ '"' + x  + '"' for x in columns ])
            else:
                line = "\t".join(columns)

            if outputfile:
                outputfile.write(line)
                outputfile.write('\n')
            else:
                if sys.version < '3':
                    print(line.encode(settings.encoding))
                else:
                    print(line)

        if settings.autooutput:
            outputfile.close()
        elif outputfile:
            outputfile.flush()
    except Exception as e:
        if settings.ignoreerrors:
            print("ERROR: An exception was raised whilst processing " + filename, e, file=sys.stderr)
        else:
            raise

if __name__ == "__main__":
    main()

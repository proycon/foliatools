#!/usr/bin/env python3

"""This tool is a FoLiA-aware wrapper around langid.py and provides languages identification on FoLiA documents"""

import sys
import os.path
import argparse
import glob
import shutil
import folia.main as folia
from langid.langid import LanguageIdentifier, model
from socket import getfqdn
from foliatools import VERSION as TOOLVERSION
from foliatools.foliavalidator import validate

LANG123 = { 'af': 'afr', 'am':'amh', 'an':'arg', 'ar':'ara', 'as':'asm', 'az':'aze', 'be':'bel', 'bg':'bul', 'bn':'ben', 'br':'bre', 'bs':'bos', 'ca':'cat', 'cs':'ces', 'cy':'cym', 'da':'dan', 'de':'deu', 'dz':'dzo', 'el':'ell', 'en':'eng', 'eo':'epo', 'es':'spa', 'et':'est', 'eu':'eus', 'fa':'fas', 'fi':'fin', 'fo':'fao', 'fr':'fra', 'ga':'gle', 'gl':'glg', 'gu':'guj', 'he':'heb', 'hi':'hin', 'hr':'hrv', 'ht':'hat', 'hu':'hun', 'hy':'hye', 'id':'ind', 'is':'isl', 'it':'ita', 'ja':'gap', 'jv':'jav', 'ka':'kat', 'kk':'kaz', 'km':'khm', 'kn': 'kan', 'ko':'kon', 'ku':'kur', 'ky':'kir', 'la':'lat', 'lb':'ltz', 'lo': 'lao', 'lt':'lit', 'lv': 'lav', 'mg':'mlg', 'mk':'mkd', 'ml':'mal', 'mn':'mon', 'mr':'mar', 'ms':'msa', 'mt':'mlt', 'nb':'nob', 'ne':'nep', 'nl':'nld', 'nn':'nno', 'no':'nor', 'oc':'oci', 'or':'ori', 'pa':'pan', 'pl':'pol', 'ps':'pus', 'pt':'por', 'qu':'que', 'ro':'ron', 'ru':'rus', 'rw':'kin', 'se':'sme', 'si':'sin', 'sk':'slk', 'sl':'slv', 'sq':'sqi', 'sr':'srp', 'sv':'swe', 'sw':'swa', 'ta':'tam', 'te':'tel', 'th':'tha', 'tl':'tgl', 'tr':'tur', 'ug':'uig', 'uk':'ukr', 'ur':'urd', 'vi':'vie', 'vo':'vol', 'wa':'wln', 'xh':'xho', 'zh':'zho', 'zu':'zul' }

LANG321 = { v: k for k, v in LANG123.items() }

LANGSET = "https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/iso639_3.foliaset"

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v','-V','--version',help="Show version information", action='version', version="FoLiA-tools v" + TOOLVERSION + ", using FoLiA v" + folia.FOLIAVERSION + " with library FoLiApy v" + folia.LIBVERSION, default=False)
    parser.add_argument('-n', '--dryrun',help="Dry run, do not write files (outputs to stdout)", action='store_true', default=False)
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml",required=False)
    parser.add_argument('-l','--languages', type=str,help="Constrain possible languages (comma separated list of ISO-639-3 codes)", action='store',required=False)
    parser.add_argument('-t','--types', type=str,help="Constrain to the following structural elements (comma separated list of FoLiA structural element tags, e.g. 's' for sentence, 'p' for paragraph). Defaults to annotating EVERY structural element.", action='store',required=False)
    parser.add_argument('-T','--textclass', type=str,help="Use the specified textclass (default: current)", action='store',required=False, default="current")
    parser.add_argument('-c','--confidence', type=float, help="Confidence threshold, anything below this will be pruned or set to the fallback language (if set)", action='store')
    parser.add_argument('-F','--fallback', type=str, help="Fallback language, everything not meeting the confidence threshold will be set to this language (with a low confidence value of 0.1", action='store')
    parser.add_argument('--verbose',help="Output verbose information", action='store_true')
    parser.add_argument('files', nargs='+', help='Input files')
    args = parser.parse_args()

    success = process(*args.files, **args.__dict__)
    sys.exit(0 if success else 1)

def processdoc(doc, **kwargs):
    identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
    if 'languages' in kwargs and kwargs['languages']:
        identifier.set_languages(kwargs['languages'].split(','))
    if 'confidence' in kwargs:
        confidencethreshold = kwargs['confidence']
    else:
        confidencethreshold = 0.0
    if 'types' in kwargs and kwargs['types']:
        types = tuple([ folia.XML2CLASS[t] for t in kwargs['types'].split(',') ])
    else:
        types = tuple([ folia.AbstractStructureElement ])
    doc.processor = folia.Processor.create(name="folialangid", version=TOOLVERSION, src="https://github.com/proycon/foliatools")
    doc.declare(folia.AnnotationType.LANG, set=LANGSET)
    for e in doc.data[0].select(types):
        try:
            text = e.text(cls=kwargs.get("textclass","current"))
        except folia.NoSuchText:
            continue #ok, no text, fine with me, nothing to do then
        if text.strip():
            lang, confidence = identifier.classify(text)
            if kwargs.get('verbose'):
                print(repr(e), lang, confidence,file=sys.stderr)
            if e.accepts(folia.LangAnnotation, raiseexceptions=False):
                if confidence > confidencethreshold:
                    e.append(folia.LangAnnotation, set=LANGSET,cls=LANG123[lang], confidence=confidence)
                elif 'fallback' in kwargs:
                    e.append(folia.LangAnnotation, set=LANGSET,cls=kwargs['fallback'], confidence=0.1)

def process(*files, **kwargs):
    success = True
    for file in files:
        if os.path.isdir(file):
            r = process(list(glob.glob(os.path.join(file, "*." + kwargs['extension'] )) ), **kwargs)
            if r != 0:
                success = False
        elif os.path.isfile(file):
            if kwargs.get('verbose'): print("Loading ", file ,file=sys.stderr)
            doc = folia.Document(file=file,autodeclare=True)
            if kwargs.get('verbose'): print("Processing ", file ,file=sys.stderr)
            processdoc(doc, **kwargs)
            if kwargs.get('dryrun'):
                print(doc.xmlstring())
            else:
                if kwargs.get('verbose'): print("Saving ", file ,file=sys.stderr)
                doc.save(doc.filename + ".upgraded")
    return success

if __name__ == "__main__":
    main()

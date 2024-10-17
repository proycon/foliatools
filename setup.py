#! /usr/bin/env python
# -*- coding: utf8 -*-

import os
import io
from setuptools import setup


def read(fname):
    return io.open(os.path.join(os.path.dirname(__file__), fname),'r',encoding='utf-8').read()

setup(
    name = "FoLiA-tools",
    version = "2.5.8", #also change in __init__.py
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("FoLiA-tools contains various Python-based command line tools for working with FoLiA XML (Format for Linguistic Annotation)"),
    license = "GPL-3.0-only",
    keywords = ["nlp", "computational linguistics", "search", "folia", "annotation"],
    url = "https://proycon.github.io/folia",
    packages=['foliatools'],
    long_description=read('README.rst'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points = {
        'console_scripts': [
            'folia2txt = foliatools.folia2txt:main',
            'folia2annotatedtxt = foliatools.folia2annotatedtxt:main',
            'foliafreqlist = foliatools.foliafreqlist:main',
            'foliavalidator = foliatools.foliavalidator:main',
            'foliamerge = foliatools.foliamerge:main',
            'foliaerase = foliatools.foliaerase:main',
            'folia2columns = foliatools.folia2columns:main',
            'folia2dcoi = foliatools.folia2dcoi:main',
            'folia2html = foliatools.folia2html:main',
            'folia2salt = foliatools.folia2salt:main',
            'foliaquery = foliatools.foliaquery:main',
            'foliaquery1 = foliatools.foliaquery1:main', #old version
            'foliatextcontent = foliatools.foliatextcontent:main',
            'dcoi2folia = foliatools.dcoi2folia:main',
            'conllu2folia = foliatools.conllu2folia:main',
            'transcribedspeech2folia = foliatools.transcribedspeech2folia:main',
            'rst2folia = foliatools.rst2folia:main',
            'txt2folia = foliatools.txt2folia:main',
            'tei2folia = foliatools.tei2folia:main',
            'foliacat = foliatools.foliacat:main',
            'folia2rst = foliatools.folia2rst:main',
            'foliacorrect = foliatools.foliacorrect:main',
            'foliacount = foliatools.foliacount:main',
            'foliaid = foliatools.foliaid:main',
            'foliaspec = foliatools.foliaspec:main',
            'foliaspec2json = foliatools.foliaspec2json:main',
            'foliaspec2rdf = foliatools.foliaspec2rdf:main',
            'alpino2folia = foliatools.alpino2folia:main',
            'foliatree = foliatools.foliatree:main',
            'foliasetdefinition = foliatools.foliasetdefinition:main',
            'foliaeval = foliatools.foliaeval:main',
            'foliaupgrade = foliatools.foliaupgrade:main',
            'folialangid = foliatools.folialangid:main',
            'foliabench = foliatools.foliabench:main',
            'foliasplit = foliatools.foliasplit:main',
            'folia2stam = foliatools.folia2stam:main',
        ]
    },
    #include_package_data=True,
    package_data = {'foliatools': ['*.xsl']},
    install_requires=['folia >= 2.5.9', 'lxml >= 2.2','docutils', 'pyyaml', 'langid','conllu', 'requests','stam >= 0.4.0']
)

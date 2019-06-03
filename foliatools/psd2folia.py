#!/usr/bin/env python3
#-*- coding:utf-8 -*-

#---------------------------------------------------------------
# Parsed files to FoLiA Converter
#   by Maarten van Gompel
#   Centre for Language Studies
#   Radboud University Nijmegen
#   proycon AT anaproy DOT nl
#
#   Licensed under GPLv3
#
# This script converts parsed files in the UPenn Historical Corpus format
# (https://www.ling.upenn.edu/hist-corpora/annotation/index.html) to FoLiA
#---------------------------------------------------------------

import argparse
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

grammar = Grammar(r"""
    body = rootnode+
    rootnode = lpar ws? node+ ws? rpar ws?
    node = lpar ws? type ws (leaf / node+) ws? rpar ws?
    leaf = lpar ws? type ws value ws? rpar ws?
    lpar = "("
    rpar = ")"
    ws          = ~r"[\s\n\r]*"
    text        = ~r"[^()]+"
    type        = text
    value       = text
""")

class PSDVisitor(NodeVisitor):
    def visit_node(self, node, visited_children):
        pass


def main():
    parser = argparse.ArgumentParser(description="This tool converts parsed files in the UPenn Historical Corpus format (https://www.ling.upenn.edu/hist-corpora/annotation/index.html) to FoLiA.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--syntaxset', type=str,help="The set definition to use for syntax", action='store',default="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/penn-treebank-syntax.foliaset.ttl",required=False)
    parser.add_argument('--posset', type=str,help="The set definition to use for part-of-speech", action='store',default="https://raw.githubusercontent.com/proycon/folia/master/setdefinitions/penn-treebank-tagset.foliaset.ttl",required=False)
    parser.add_argument('files', nargs='+', help='Input files (*.psd)')
    args = parser.parse_args()
    for file in args.files:
        with open(file, 'r', encoding='utf-8') as f:
            tree = grammar.parse(f.read())
            print(tree)


if __name__ == '__main__':
    main()

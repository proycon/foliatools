#!/usr/bin/env python3

"""Convert the FoLiA specification from YAML to JSON. This is mostly an internal tool with little public use."""

from __future__ import print_function, unicode_literals, division, absolute_import

import sys
import os
import json
import yaml

#Load specification
spec = yaml.load(open(sys.argv[1],'r'))

if spec is None:
    print("FoLiA Specification file folia.yml could not be found in " + ", ".join(specfiles) ,file=sys.stderr)

def main(var=None):
    try:
        var = sys.argv[1]
        if var[0] == '-': var = None
    except:
        var = None
    if var:
        print(var + ' = ' + json.dumps(spec, sort_keys=True, indent=4) + ';')
    else:
        print(json.dumps(spec, sort_keys=True, indent=4))

if __name__ == '__main__':
    main()

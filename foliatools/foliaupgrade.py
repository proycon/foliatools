#!/usr/bin/env python3

import sys
import os.path
import argparse
import glob
import folia.main as folia
from foliatools.foliavalidator import validate

def main():
    parser = argparse.ArgumentParser(description="", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-V', '--version',help="Output version information", action='store_true')
    parser.add_argument('-n', '--dryrun',help="Dry run, do not write files", action='store_true')
    parser.add_argument('-E','--extension', type=str,help="Extension", action='store',default="xml",required=False)
    parser.add_argument('files', nargs='+', help='Input files')
    args = parser.parse_args()

    if args.version:
        print("FoLiA " + folia.FOLIAVERSION + ", library version " + folia.LIBVERSION,file=sys.stderr)
        sys.exit(0)

    success = process(*args.files, **args)
    sys.exit(0 if success else 1)

def process(*files, **kwargs):
    success = False
    for file in files:
        if os.path.isdir(file):
            r = process(list(glob.glob(os.path.join(file, "*." + kwargs['extension'] )) ), **kwargs)
            if r != 0:
                success = False
        elif os.path.isfile(file):
            doc = validate(file,schema=None,quick=False,deep=False, stricttextvalidation=True,autodeclare=True,output=True)
            if doc is not False:
                print("Upgrading " + doc.filename,file=sys.stderr)
                if not kwargs.dryrun:
                    doc.save()
            else:
                success  = False
    return success

if __name__ == "__main__":
    main()

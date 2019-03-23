#!/bin/bash

boldred=${bold}$(tput setaf 1) #  red
boldgreen=${bold}$(tput setaf 2) #  green
boldblue=${bold}$(tput setaf 4) #  blue
normal=$(tput sgr0)

FAILURE=0

for f in ../folia/examples/*.folia.xml; do #the example/test data is in a git submodule
    if [[ $f = *"deep"* ]]; then
        echo "Running FoLiA validator (DEEP!) on $(basename $f)" >&2
        foliavalidator -d $f
    else
        echo "Running FoLiA validator (shallow) on $(basename $f)" >&2
        foliavalidator $f
    fi
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
done

echo "Running folia2txt" >&2
folia2txt test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff test.tmp test.txt > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=0
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi

echo "Running folia2columns" >&2
folia2columns -c id,text,pos,lemma test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff test.tmp test.columns.txt > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi


echo "Running folia2annotatedtxt" >&2
folia2annotatedtxt -c id,text,pos,lemma test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff test.tmp test.annotated.txt > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi

echo "Running folia2html" >&2
folia2html test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff -ZBEb test.tmp test.html > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi


echo "Running foliaquery1" >&2
foliaquery1 --text "zin" test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff test.tmp test.query1 > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi

echo "Running foliaquery1 (2)" >&2
foliaquery1 --pos "{(A|T).*} {N\(.*}" test.xml > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
    diff test.tmp test.query2 > test.diff
    if [ $? -ne 0 ]; then
        echo "...${boldred}FAILED${normal}" >&2
        FAILURE=1
        cat test.diff
    else
        echo "...${boldgreen}OK${normal}" >&2
    fi
fi

echo "Running rst2folia" >&2
rst2folia --traceback test.rst > test.tmp
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
  foliavalidator test.tmp
  if [ $? -ne 0 ]; then
      echo "...VALIDATOR ${boldred}FAILED${normal}" >&2
      FAILURE=1
  else
      echo "...${boldgreen}OK${normal}" >&2
  fi
fi

echo "Running conllu2folia" >&2
conllu2folia test.fr.conllu
if [ $? -ne 0 ]; then
    echo "...${boldred}FAILED${normal}" >&2
    FAILURE=1
else
  foliavalidator test.fr.folia.xml
  if [ $? -ne 0 ]; then
      echo "...VALIDATOR ${boldred}FAILED${normal}" >&2
      FAILURE=1
  else
      echo "...${boldgreen}OK${normal}" >&2
  fi
fi

exit $FAILURE



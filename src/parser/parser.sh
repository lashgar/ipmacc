#!/bin/bash

t=$0
#t=`pwd`/$0
path=${t%/*}

if [ "$1" == "" ] ; then
    echo "usage: parser scanner-xml-file"
    exit 255
fi

if [ ! -e $path/oaccparser ] ; then
    echo missing parser... performing the make
    cd $path
    make
fi

# analyze individual OpenACC directive and clause.
# report unsupported statements
python $path/oaccsyntaxchk_clauses.py -f $1
if [ "$?" == "255" ] ; then
    echo "parser exits due to previous errors"
    exit 255
fi

# analyze the OpenACC enhanced C code
# stall for unsupported directive nest
## NEW VERSION
python $path/oaccsyntaxchk_directives.py -f $1
## OLD VERSION
##python $path/codeanalyzer.py -f $1 
#python $path/codeanalyzer.py -f $1 | $path/oaccparser
##echo $?
if [ "$?" == "255" ] ; then
    echo "error: improper use of OpenACC in the C code"
    exit 255
fi

exit 0

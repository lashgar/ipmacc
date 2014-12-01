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

# analyze OpenACC directive and clause.
# report unsupported statements
python $path/pragmadecomposer.py -f $1
if [ "$?" == "255" ] ; then
    echo "parser exits due to previous errors"
    exit 255
fi

# analyze the OpenACC enhanced C code
python $path/codeanalyzer.py -f $1 | $path/oaccparser
#echo $?
if [ "$?" == "255" ] ; then
    echo "error: improper use of OpenACC in the C code"
    exit 255
fi

exit 0

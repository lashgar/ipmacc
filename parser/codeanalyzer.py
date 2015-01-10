import sys
import re
import xml.etree.ElementTree as ET
from optparse import OptionParser

lastchar='0'

def nextchar(ch):
    global lastchar
    print ch
    lastchar=ch

def error(prompt):
    print('error: '+prompt)
    exit(-1)

def sequentialParser(root):
    if root.tag=='pragma' and root.attrib.get('directive')=='kernels':
        nextchar('K')
    elif root.tag=='pragma' and root.attrib.get('directive')=='data':
        nextchar('D')
    elif root.tag=='pragma' and root.attrib.get('directive')=='loop':
        nextchar('L')
    elif root.tag=='pragma' and root.attrib.get('directive')=='cache':
        nextchar('M')
    elif root.tag=='pragma' and (root.attrib.get('directive')=='enter' or root.attrib.get('directive')=='exit'):
        nextchar('E')
    elif root.tag=='pragma' and root.attrib.get('directive')=='parallel':
        nextchar('A')
        error('`parallel` not yet supported')
    elif root.tag=='scanner':
        nextchar('S')
    elif root.tag=='c':
        nextchar('C')
    elif root.tag=='for':
        nextchar('F')

    for child in root:
        sequentialParser(child)

    if root.tag=='pragma' and root.attrib.get('directive')=='kernels':
        nextchar('k')
    elif root.tag=='pragma' and root.attrib.get('directive')=='data':
        nextchar('d')
    elif root.tag=='pragma' and root.attrib.get('directive')=='loop':
        nextchar('l')
    elif root.tag=='pragma' and root.attrib.get('directive')=='cache':
        nextchar('m')
    elif root.tag=='pragma' and root.attrib.get('directive')=='parallel':
        nextchar('a')
    elif root.tag=='for':
        nextchar('f')

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to input xml", metavar="FILE", default="")
(options, args) = parser.parse_args()

if options.filename=="":
    parser.print_help()
    exit(-1)

tree = ET.parse(options.filename)
root = tree.getroot()

sequentialParser(root)


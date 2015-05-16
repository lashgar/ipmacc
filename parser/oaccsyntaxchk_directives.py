import sys
import re
import xml.etree.ElementTree as ET
from optparse import OptionParser

def error(prompt):
    print('error: '+prompt)
    exit(-1)

def assert_syntax(root, parent_map, invalid_parents):
    troot=parent_map[root]
    #print root.tag+' '+root.attrib.get('directive')
    while troot.tag!='scanner':
        for p in invalid_parents:
            if troot.tag=='pragma':
                #print p+' != '+troot.attrib.get('directive')
                if p==troot.attrib.get('directive'):
                    error('invalid syntax: `'+root.attrib.get('directive')+'\' is not allowed in `'+p+'\'')
        troot=parent_map[troot]

def sequentialParser(root, parent_map):
    # invalid_parents = ['atomic', 'cache', 'data', 'enter', 'exit', 'kernels', 'loop', 'parallel']
    invalid_parents = []
    if root.tag=='pragma' and root.attrib.get('directive')=='kernels':
        invalid_parents = ['atomic', 'cache', 'kernels', 'loop', 'parallel']

    elif root.tag=='pragma' and root.attrib.get('directive')=='data':
        invalid_parents = ['atomic', 'cache', 'kernels', 'loop', 'parallel']

    elif root.tag=='pragma' and root.attrib.get('directive')=='loop':
        invalid_parents = ['atomic']

    elif root.tag=='pragma' and root.attrib.get('directive')=='cache':
        invalid_parents = ['atomic']

    elif root.tag=='pragma' and (root.attrib.get('directive')=='enter' or root.attrib.get('directive')=='exit'):
        invalid_parents = ['atomic', 'cache', 'kernels', 'loop', 'parallel']

    elif root.tag=='pragma' and root.attrib.get('directive')=='atomic':
        invalid_parents = []

    elif root.tag=='pragma' and root.attrib.get('directive')=='parallel':
        invalid_parents = ['atomic', 'cache', 'kernels', 'loop', 'parallel']
        error('`parallel` not yet supported')

    elif root.tag=='for':
        invalid_parents = ['atomic']

    elif root.tag=='scanner' or root.tag=='c':
        righton = True

    if root.tag=='pragma':
        assert_syntax(root, parent_map, invalid_parents)

    for child in root:
        sequentialParser(child, parent_map)

parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to input xml", metavar="FILE", default="")
(options, args) = parser.parse_args()

if options.filename=="":
    parser.print_help()
    exit(-1)

tree = ET.parse(options.filename)
root = tree.getroot()

parent_map = dict((c, p) for p in tree.getiterator() for c in p)
#for c, p in parent_map.iteritems():
#    print c.tag+' > '+p.tag
sequentialParser(root, parent_map)
#print 'i don\'t see any error!'


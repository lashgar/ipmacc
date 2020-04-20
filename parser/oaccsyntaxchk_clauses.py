import sys
import re
import xml.etree.ElementTree as ET
from optparse import OptionParser

DEBUG=False
lastchar='0'


sys.path.extend(['.', '..'])
from utils_clause import clauseDecomposer


def nextchar(ch):
    global lastchar
    print ch
    lastchar=ch

def error(directive,clause,clauses):
    print 'error: invalid clause `'+clause+'` for `'+directive+'`'
    print 'available clauses are: ',', '.join(clauses)
    exit(-1)

def lookup(clauses,clause):
    try:
        clauses.index(clause)
        return True
    except:
        return False
#
#def clauseDecomposer(clause):
#    clist=[]
#    index=1
#    if len(clause)>0:
#        lastchar=clause[0]
#        while index<len(clause):
#            if DEBUG: print str(len(clist))+'->'+lastchar
#            tclause=''
#            # read spacing
#            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
#                tclause+=lastchar
#                lastchar=clause[index]
#                index+=1
#            # read clause name
#            while (str.isalpha(lastchar) or str.isdigit(lastchar) or lastchar=='_'):
#                tclause+=lastchar
#                if(index<len(clause)):
#                    lastchar=clause[index]
#                    index+=1
#                else:
#                    break
#            # read spacing
#            while index<len(clause) and (lastchar==' ' or lastchar=='\t'):
#                tclause+=lastchar
#                lastchar=clause[index]
#                index+=1
#            # read parenteces
#            if lastchar=='(':
#                depth=1
#                while index<len(clause) and (not (lastchar==')' and depth==0)):
#                    tclause+=lastchar
#                    lastchar=clause[index]
#                    index+=1
#                    if   lastchar=='(':
#                        depth+=1
#                    elif lastchar==')':
#                        depth-=1
#                tclause+=lastchar
#                if index<len(clause):
#                    lastchar=clause[index]
#                    index+=1
##            tclause+=lastchar
#            clist.append(tclause)
#    return clist

def sequentialParser(root):
    if root.tag=='pragma':
        clauses=root.attrib.get('clause')
        #k=clauses.replace('independent','independent()')
        #regex=re.compile(r'([A-Za-z0-9\ ]+)([\(])([A-Za-z0-9\ ,\[\]\:]*)([\)])')
        #regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
        clausesList=clauseDecomposer(clauses)
#        for it in regex.findall(clauses):
        if DEBUG:
            print 'Clauses -> '+'<>'.join(clausesList)
        for it in clausesList:
            #clause=it[0].strip()
            clause=it.split('(')[0].strip()
            if root.attrib.get('directive')=='kernels':
#                valid_clauses=['if', 'async',
#                                'create', 'present',
#                                'copy', 'copyin', 'copyout',
#                                'present_or_copy', 'present_or_copyin', 'present_or_copyout', 'present_or_create',
#                                'pcopy', 'pcopyin', 'pcopyout',
#                                'deviceptr']
                avail_clauses=[ 'if', 'async',
                                'create', 'present',
                                'copy', 'copyin', 'copyout',
                                'present_or_copy', 'present_or_copyin', 'present_or_copyout', 'present_or_create',
                                'pcopy', 'pcopyin', 'pcopyout',
                                'deviceptr',
                                'compression', 'compression_copy', 'compressions_copyin', 'compression_copyout',
                                'ccopy', 'ccopyin', 'ccopyout',
                                'present_or_compression_copy', 'present_or_compression_copyin', 'present_or_compression_copyout', 'present_or_compression_create',
                                'pccopy', 'pccopyin', 'pccopyout']
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='data':
#                valid_clauses=[ 'if',
#                                'create', 'present',
#                                'copy', 'copyin', 'copyout',
#                                'present_or_copy', 'present_or_copyin', 'present_or_copyout', 'present_or_create',
#                                'pcopy', 'pcopyin', 'pcopyout', 'pcreate',
#                                'deviceptr']
                avail_clauses=[ 'create', 'present',
                                'copy', 'copyin', 'copyout',
                                'present_or_copy', 'present_or_copyin', 'present_or_copyout', 'present_or_create',
                                'pcopy', 'pcopyin', 'pcopyout',
                                'deviceptr',
                                'compression', 'compression_copy', 'compressions_copyin', 'compression_copyout',
                                'ccopy', 'ccopyin', 'ccopyout',
                                'present_or_compression_copy', 'present_or_compression_copyin', 'present_or_compression_copyout', 'present_or_compression_create',
                                'pccopy', 'pccopyin', 'pccopyout']
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='loop':
#                valid_clauses=['collapse', 'gang', 'worker', 'vector', 'seq', 'independent', 'private', 'reduction']
                avail_clauses=['gang', 'vector', 'seq', 'independent', 'private', 'reduction',
                                # ipmacc additions
                                'smc', 'perforation' ]
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='parallel':
#                valid_clauses=['if', 'async', 'num_gangs', 'num_workers', 'vector_length', 'reduction',
#                                'copy', 'copyin', 'copyout', 'create',
#                                'present', 'present_or_copy', 'present_or_copyin', 'present_or_copyout', 'present_or_create',
#                                'pcopy', 'pcopyin', 'pcopyout', 'pcreate',
#                                'deviceptr', 'private', 'first_private']
                clause='parallel'
                avail_clauses=[]
                error('',clause,avail_clauses)
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='enter':
                avail_clauses=['data', 'copyin', 'create', 'present_or_create', 'present_or_copyin']
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='exit':
                avail_clauses=['data', 'copyout']
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

            elif root.attrib.get('directive')=='atomic':
                avail_clauses=['capture'] # 'read', 'write', 'update', 
                if not lookup(avail_clauses,clause):
                    error(root.attrib.get('directive'),clause,avail_clauses)

    for child in root:
        sequentialParser(child)


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
exit(0)

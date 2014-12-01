from __future__ import print_function
import sys
import xml.etree.ElementTree as ET
import os

sys.path.extend(['.', '..', './pycparser/'])

from pycparser import c_parser, c_ast

def assignmentRecursive(astNode):
    print('Not implemented!')

def declareRecursive(astNode):
#    childCode=[]
#    for child in astNode:
#        childCode.append(declareRecursive(child))
    #print(astNode.tag)
    code=''
    if astNode.tag=='PtrDecl':
        # one child
        code='(dynamic)*'+declareRecursive(astNode[0])
    elif astNode.tag=='ArrayDecl' and len(astNode)==2:
        # array of known size
        code='('+declareRecursive(astNode[1])+')*'+declareRecursive(astNode[0])
    elif astNode.tag=='ArrayDecl' and len(astNode)==1:
        # array of unkown size
        code='(unkown)*'+declareRecursive(astNode[0])
    elif astNode.tag=='BinaryOp':
        code='('+declareRecursive(astNode[0])+astNode.get('uid')+declareRecursive(astNode[1])+')'
    elif astNode.tag=='Constant':
        code=astNode.get('uid').split(',')[1].strip()
    elif astNode.tag=='ID':
        code=astNode.get('uid')
    elif astNode.tag=='IdentifierType':
        code='sizeof('+astNode.get('uid')+')'
    else:
        for child in astNode:
            code=code+declareRecursive(child)
    return code

def initilizieRecursive(astNode):
    code=''
    for child in astNode:
        code=code+'-'+initilizieRecursive(child)
    return (astNode.get('uid') if astNode.tag=='ID' else '')+code

#kernelsVars=[]
#kernelsTyps=[]
#varName=['a', 'c', 'k']
#funcName=['main', 'main', 'main']
#for cn in range(0,len(varName)):
def var_find_size(root, varName, funcName):
    # go through all functions in the code (C/C++ code)
    # find the function which the kernel is called there
    # then find the type of all variables
    for func in root.findall(".//FuncDef"):
        if func.find('Decl').get('uid').strip()==funcName.strip():
            # print('inside '+funcName[cn])
            funcBody=func.find('Compound')
            for var in funcBody.findall(".//Decl"):
                # single variable Decl
                if var.get('uid').strip()==varName.strip():
                    # print('============ var '+varName+' found')
                    init='unitilialized'
                    if len(var)==2:
                        # print('declaration and initialization')
                        size = declareRecursive(var[0])
                        init = initilizieRecursive(var[1])
                    elif len(var)==1:
                        #print('only declerations')
                        size = declareRecursive(var[0])
                    else:
                        print('unexpected number of chiled')
                        exit(1)
                    # check for unknow sizes and dynamic allocations
                    if size.find('unkown')!=-1:
                        print('Unable to determine the array size')
                    if size.find('dynamic')!=-1:
                        print('dynamic allocation detected')
                        # find all assignment expressions and look for allocations
                        # ignore C++ new statements for now
                        #for assignm in funcBody.findall(".//Assignment"):
                            #if assignm[0].get('uid').strip()==varName.strip():
                                #allocationSize = assignmentRecursive(assignm)
                    print('var('+varName+')-> size='+size+' '+'('+init+')')
                    break



filehandle = open('dummy2.c', 'r')
#filehandle = open('reverse_noinclude.c', 'r')
#filehandle = open('reverse.c', 'r')
text = ''.join(filehandle.readlines())
#print(text)

# create a pycparser
parser = c_parser.CParser()
ast = parser.parse(text, filename='<none>')

# generate the XML tree
ast.show()
codeAstXml = open('code_ast.xml','w')
ast.showXml(codeAstXml)
codeAstXml.close()
tree = ET.parse('code_ast.xml')
root = tree.getroot()

var_find_size(root, 'c', 'main')

os.remove('code_ast.xml')

from __future__ import print_function
import sys
import xml.etree.ElementTree as ET
import os

sys.path.extend(['.', '..', './pycparser/'])

from pycparser import c_parser, c_ast

filehandle = open('dummy3.c', 'r')
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

kernelsVars=[]
kernelsTyps=[]
kernelNames=['__ungenerated_kernel_function_region__0']
for kn in kernelNames:
    # go through all functions in the code (C/C++ code)
    # find the function which the kernel is called there
    # then find the type of all variables
    for func in root.findall(".//FuncDef"):
        kernelFound=0
        kernelVars=[]
        kernelTyps=[]
        print('we have found '+str(len(func.findall(".//FuncCall/ID")))+' function calls')
        for fcall in func.findall(".//FuncCall/ID"):
            if str(fcall.get('uid')).strip()==kn.strip():
                kernelFound=1
                #print(fcall.get('uid'))
        if kernelFound==1:
            print('<'+kn+'> is found in <'+func.find('Decl').get('uid')+'>')
            # go through all declerations and find the varibales
            funcBody=func.find('Compound')
            for var in funcBody.findall(".//Decl"):
                # single variable Decl
                kernelVars.append(var.get('uid'))
                kernelTyps.append(var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl")))*'*'))
#                print('< '+var.get('uid')+' > is defined as <'+var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl")))*'*')+'>')
            kernelsVars.append(kernelVars)
            kernelsTyps.append(kernelTyps)
            break

for i in range(0,len(kernelsVars)):
    var=kernelsVars[i]
    typ=kernelsTyps[i]
    print('=======> kernel #'+str(i)+':')
    for g in range(0,len(var)):
        print(var[g]+'->'+typ[g])

os.remove('code_ast.xml')


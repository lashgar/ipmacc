import sys
import re
import xml.etree.ElementTree as ET
#from termcolor import colored
import os

sys.path.extend(['.', '..', './pycparser/'])
from pycparser import c_parser, c_ast

from subprocess import call, Popen, PIPE
import tempfile

from optparse import OptionParser

# config control
ENABLE_INDENT=True
DEBUG=1
VERBOSE=1

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''

class codegen(object):
    def __init__(self, fname=None, foname=None):
        self.oacc_kernelId=0     # number of kernels which are replaced by function calls
        self.oacc_kernels=[]     # array of kernels' roots (each element of array is ElementTree)
        self.oacc_kernelsParent=[]   # array of functions name, indicating which function is the parent of kernel (associated with each elemnt in self.oacc_kernels)
        self.oacc_kernelsVarNams=[] # list of array of variables defined in the kernels' call scope
        self.oacc_kernelsVarTyps=[] # list of array of type of variables defined in the kernels' call scope
        self.oacc_kernelsLoopIterators=[]   # list of array of iterators

        self.oacc_copyId=0  # number of copys which are replaced by function calls
        self.oacc_copys=[]  # array of copys' expression (each element is string)
        self.oacc_copysParent=[]   # array of functions name, indicating the function which is the parent of copy (associated with each elemnt in self.oacc_copys)
        self.oacc_copysVarNams=[] # list of array of variables defined in the copys' call scope
        self.oacc_copysVarTyps=[] # list of array of type of variables defined in the copys' call scope
        
        self.code='' # intermediate generated C code
        self.code_include='' # .h code including variable decleration and function prototypes
        self.code_kernel='' # peace of code generated for kernels

        # variable mapper
        self.varmapper=[]   # tuple of (function_name, host_variable_name, device_variable_name)
        self.varmapper_allocated=[]
        self.prefix_varmapper = '__autogen_device_'
        self.suffix_present = '_prstn'

        # constants
        self.prefix_kernel='__ungenerated_kernel_region_'
        self.prefix_kernel_gen='__generated_kernel_region_'
        self.prefix_datacp='__ungenerated_data_copy_'
        self.prefix_dataalloc='__ungenerated_data_alloc_'
        self.prefix_kernel_uid='__kernel_getuid'

        # ast tree
        self.astRoot=0
    
    #
    # dump final openacc-equivalent function calls (data copies, kernels, ...)
    #
    def oacc_copyWb(self,id,expression):
        fhandle=open(self.prefix_datacp+str(id)+'.xml','w')
        fhandle.write(expression)
        fhandle.close()

    def code_kernelDump(self,id):
        if len(self.oacc_kernels)<id:
            print 'kernel '+str(id)+'not available'
        else:
            #self.oacc_kernels[id].getroottree().write('dummy.xml')
            old_stdout = sys.stdout
            sys.stdout = open(self.prefix_kernel+str(id)+'.xml','w')
            ET.dump(self.oacc_kernels[id])
            sys.stdout = old_stdout
    
    def code_kernelPrint(self,id):
        if len(self.oacc_kernels)<id:
            print 'kernel '+str(id)+'not available'
        else:
            self.code_kernelDescendentPrint(self.oacc_kernels[id],0)

    def code_kernelDescendentPrint(self, root, depth):
        if root.getchildren()==[]:
            print str(root.text)
        else:
            print bcolors.WARNING+str('\t'*depth)+str(root.tag)+str(root.attrib)+bcolors.ENDC
            for child in root:
                self.code_kernelDescendentPrint(child,depth+1)
    #
    def oacc_data_clauseparser(self,clause,type,inout,present):
        # parse openacc data clause and return correponding type (copyin, copyout, copy, pcopyin, pcopyout, pcopy)
        code=''
        regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        for i in regex.findall(clause):
            if str(i[0]).strip()==type:
                for j in str(i[3]).split(','):
                    #tcode=tcode+'<copy '
                    tcode=''
                    # varname
                    tcode=tcode+'varname="'+str(j).replace(' ','').split('[')[0]+'" '
                    # in/out
                    tcode=tcode+'in="'+inout+'" '
                    #tcode=tcode+'in="'+('true' if inout=='in' else 'false')+'" '
                    # present
                    tcode=tcode+'present="'+present+'" '
                    # dimensions
                    regex2 = re.compile(r'\[(.+?)\]')
                    dims=regex2.findall(str(j).replace(' ',''))
                    for dim in range(0,len(dims)):
                        tcode=tcode+'dim'+str(dim)+'="'+dims[dim]+'" '
                    # end tag
                    #tcode=tcode+'></copy>\n'
                    #tcode=tcode+'\n'
                    code=code+tcode+'\n'
        return code

    def oacc_clauseparser_data(self, clauses):
        expressionIn=''
        expressionAlloc=''
        expressionOut=''
        copyoutId=-1
        # copy-in
        for it in ['copyin', 'copy']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','false')
        for it in ['pcopy', 'present_or_copy', 'pcopyin', 'present_or_copyin']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','true')
        # allocate-only
        for it in ['create']:
            expressionAlloc=expressionAlloc+self.oacc_data_clauseparser(clauses,it,'create','true')
        # copy-out
        for it in ['copyout', 'copy']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','false')
        for it in ['pcopy', 'present_or_copy', 'pcopyout', 'present_or_copyout']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','true')
        return [expressionIn, expressionAlloc, expressionOut, copyoutId]

    def oacc_clauseparser_flags(self,clause,type):
        # parse openacc clause and return if type exists
        code=''
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        for i in regex.findall(clause):
            if str(i[0]).strip()==type:
                return True
        return False

    def oacc_clauseparser_if(self,clause):
        # parse openacc `if` and return condition 
        code=''
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        for i in regex.findall(clause):
            if str(i[0]).strip()=='if':
                try:
                    return i[2].strip()
                except:
                    print 'error: expecting argument (condition) for the `if` caluse'
                    exit(-1)
        return ''

    def cuda_append_sync(self):
        return 'cudaDeviceSynchronize();'
    def cuda_append_opencondition(self,cond):
        return 'if('+cond+'){\n'
    def cuda_append_closecondition(self,cond):
        return '}\n'
    #
    # Top Level Recursive Code Analyzer
    def code_descendentRetrieve(self, root, depth):
        # parse the code's XML tree (root) and retrieve the intermediate code (self.code)
        if root.tag == 'pragma' and root.attrib.get('directive')=='kernels':
            # case 1: start of the kernel region
            # parse the clause for data (including copy, copyin, copyout, create, and similar present alternatives
            expressionIn=''
            expressionAlloc=''
            expressionOut=''
            copyoutId=-1
            [expressionIn, expressionAlloc, expressionOut, copyoutId] = self.oacc_clauseparser_data(str(root.attrib.get('clause')))
            if DEBUG>0:
                print expressionIn+'\n'+expressionAlloc+'\n'+expressionOut # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
            # * generate proper code before the kernels region:
            #   - if
            regionCondition=self.oacc_clauseparser_if(str(root.attrib.get('clause')))
            if regionCondition!='':
                self.code=self.code+self.cuda_append_opencondition(regionCondition)
            #   - copy, copyin (allocation and transfer)
            if expressionIn!='':
                self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
                self.oacc_copys.append(expressionIn)
                self.oacc_copyId=self.oacc_copyId+1
            #   - create (allocation)
            if expressionAlloc!='':
                self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
                self.oacc_copys.append(expressionAlloc)
                self.oacc_copyId=self.oacc_copyId+1
            #   - copy, copyout (allocation)
            if expressionOut!='':
                self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                copyoutId=self.oacc_copyId
                self.oacc_copys.append(expressionOut)
                self.oacc_copyId=self.oacc_copyId+1
            # * generate dummy kernel launch function call
            self.code=self.code+self.prefix_kernel+str(self.oacc_kernelId)+'();'
            self.oacc_kernelId=self.oacc_kernelId+1
            self.tag_indepLoops(root,False)
            self.oacc_kernels.append(root)
            # * generate proper code after the kernels region:
            #   - copy, copyout (transfer)
            if expressionOut!='':
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(copyoutId)+'();'
            #   - async
            if not self.oacc_clauseparser_flags(str(root.attrib.get('clause')),'async'):
                self.code=self.code+self.cuda_append_sync()
            #   - if
            if regionCondition!='':
                self.code=self.code+self.cuda_append_closecondition(regionCondition)
        elif root.getchildren()==[]:
            # case 2: no descendent is found
            if root.tag == 'for':
                # for is special case, handle it specially
                self.code=self.code+str('\t'*depth)+'for('+str(root.attrib.get('initial'))+';'+str(root.attrib.get('boundary'))+';'+str(root.attrib.get('increment'))+')'
            self.code=self.code+str(root.text)
        else:
            # case 3: go through descendents recursively
            expressionIn=''
            expressionAlloc=''
            expressionOut=''
            copyoutId=-1
            if root.tag == 'for':
                self.code=self.code+str('\t'*depth)+'for('+str(root.attrib.get('initial'))+';'+str(root.attrib.get('boundary'))+';'+str(root.attrib.get('increment'))+')'
            elif (root.tag=='pragma' and root.attrib.get('directive')=='data'):
                # parse data clauses and
                [expressionIn, expressionAlloc, expressionOut, copyoutId] = self.oacc_clauseparser_data(str(root.attrib.get('clause')))
                if DEBUG>0:
                    print expressionIn+'\n'+expressionAlloc+'\n'+expressionOut # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
                # dump pragma copyin allocation/transfer before region
                if expressionIn!='':
                    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                    self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
                    self.oacc_copys.append(expressionIn)
                    self.oacc_copyId=self.oacc_copyId+1
                # dump pragma create allocation before region
                if expressionAlloc!='':
                    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                    self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
                    self.oacc_copys.append(expressionAlloc)
                    self.oacc_copyId=self.oacc_copyId+1
                # dump pragma copyout allocation before region
                if expressionOut!='':
                    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
                    copyoutId=self.oacc_copyId
                    self.oacc_copys.append(expressionOut)
                    self.oacc_copyId=self.oacc_copyId+1
            for child in root:
                self.code_descendentRetrieve(child,depth+1)
            # dump pragma copyout transfer after the region
            if (root.tag=='pragma' and root.attrib.get('directive')=='data') and expressionOut!='':
                # dump pragma transfer after region
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(copyoutId)+'();'

    def code_descendentDump(self,filename):
        # dump the code at current stage to filename
        old_stdout = sys.stdout
        f = open(filename,'w')
        sys.stdout = f
        print self.code_include+self.code
        f.close()
        sys.stdout = old_stdout
        if ENABLE_INDENT==True:
            Popen(["indent", filename])

    #
    # VARIABLE TYPE DETECTOR FUNCTIONS: var_kernel_parentsFind, var_copy_parentsFind, var_findFuncParents, var_parseForYacc,
    def astCalcRoot(self):
        text = self.var_parseForYacc(self.code)
        if DEBUG>1:
            print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')

        # generate the XML tree
        #ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        self.astRoot = tree.getroot()

    def var_kernel_parentsFind(self):
        self.var_findFuncParents("kernel")

    def var_copy_parentsFind(self):
        self.var_findFuncParents("data")
    
    def var_findFuncParents(self,funcName):
        # find the parent of function
        # parent of function A is a function calling A
        # here, the parent is unique since the funcName is unique autogenerated name
        root = self.astRoot

        count  = self.oacc_kernelId if funcName=="kernel" else self.oacc_copyId
        prefix = self.prefix_kernel if funcName=="kernel" else self.prefix_datacp
        for id in range(0,count):
            # go through all functions in the code (C/C++ code)
            # find the function which the function is called there
            # then find the type of all variables
            kn=prefix+str(id)
            for func in root.findall(".//FuncDef"):
                funcFound=0
                funcVars=[]
                funcTyps=[]
                # print('we have found '+str(len(func.findall(".//FuncCall/ID")))+' function calls in '+str(func.find('Decl').get('uid')))
                for fcall in func.findall(".//FuncCall/ID"):
                    if str(fcall.get('uid')).strip()==kn.strip():
                        funcFound=1
                        if funcName=="kernel":
                            #self.oacc_kernelsParent.append(fcall.get('uid'))
                            self.oacc_kernelsParent.append(func.find('Decl').get('uid'))
                        else:
                            #self.oacc_copysParent.append(fcall.get('uid'))
                            self.oacc_copysParent.append(func.find('Decl').get('uid'))
                if funcFound==1:
                    # print('<'+kn+'> is found in <'+func.find('Decl').get('uid')+'>')
                    # go through all declerations and find the varibales
                    # first, function prototype
                    funcBody=func.find('Compound')              # variable defined in the body
                    if func.find('.//ParamList'):
                        funcBody.append(func.find('.//ParamList'))  # variables defined in the params
                    for var in funcBody.findall(".//Decl"):
                        # single variable Decl
                        if DEBUG>0:
                            print var.get('uid').split(',')[0]
                        funcVars.append(var.get('uid').split(',')[0])
                        funcTyps.append(var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl"))+len(var.findall(".//ArrayDecl")))*'*'))
                        #print('< '+var.get('uid')+' > is defined as <'+var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl")))*'*')+'>')
                    
                    if funcName=="kernel":
                        self.oacc_kernelsVarNams.append(funcVars)
                        self.oacc_kernelsVarTyps.append(funcTyps)
                    else:
                        self.oacc_copysVarNams.append(funcVars)
                        self.oacc_copysVarTyps.append(funcTyps)
                    break

    # YACC-friendly code generator
    def var_parseForYacc(self, InCode):
        # here  the InCode has no comment block or comment line
        # 1) instead of removing include, we put a workout:
        code="#define __attribute__(x)\n"+"#define __asm__(x)\n"+"#define __builtin_va_list int\n"+"#define __const\n"+"#define __restrict\n"+"#define __extension__\n"+"#define __inline__\n"+InCode
        #code = InCode
        #re.sub(r'(#include).*.(\n)', '', code)
        # 2) replace #define using GNU cpp
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(code)
        f.close()
        p1 = Popen(["cat", f.name], stdout=PIPE)
        p2 = Popen(["cpp", "-E"], stdin=p1.stdout, stdout=PIPE)
        code = p2.communicate()[0]
        os.remove(f.name)
        # 3) remove cpp # in the begining of file
        code=re.sub(r'(#\ ).*.(\n)', '', code)
        return code.strip()
    def assignmentRecursive(self,astNode):
        print('Not implemented!')

    def declareRecursive(self,astNode):
        # find the size of variable declered by astNode
        code=''
        if astNode.tag=='PtrDecl':
            # one child
            code='(dynamic)*'+self.declareRecursive(astNode[0])
        elif astNode.tag=='ArrayDecl' and len(astNode)==2:
            # array of known size
            code='('+self.declareRecursive(astNode[1])+')*'+self.declareRecursive(astNode[0])
        elif astNode.tag=='ArrayDecl' and len(astNode)==1:
            # array of unkown size
            # potentially function argument or dynamic allocation
            # so assume it as dynamic
            code='(dynamic)*'+self.declareRecursive(astNode[0])
        elif astNode.tag=='BinaryOp':
            code='('+self.declareRecursive(astNode[0])+astNode.get('uid')+self.declareRecursive(astNode[1])+')'
        elif astNode.tag=='Constant':
            code=astNode.get('uid').split(',')[1].strip()
        elif astNode.tag=='ID':
            code=astNode.get('uid')
        elif astNode.tag=='IdentifierType':
            code='sizeof('+astNode.get('uid')+')'
        else:
            for child in astNode:
                code=code+self.declareRecursive(child)
        return code

    def initilizieRecursive(self,astNode):
        code=''
        for child in astNode:
            code=code+'-'+self.initilizieRecursive(child)
        return (astNode.get('uid') if astNode.tag=='ID' else '')+code


    def var_find_size(self, varName, funcName, root):
        # find the size of variabl varName defined in the funcName
        # usefull for dynamic allocation and array definitions
        # NOTICE: currently dynamic allocation is not detected!

        # go through all functions in the code (C/C++ code)
        # find the function which the kernel is called there
        # then find the type of all variables
        for func in root.findall(".//FuncDef"):
            if func.find('Decl').get('uid').strip()==funcName.strip():
                # print('inside '+funcName[cn])
                funcBody=func.find('Compound')
                if func.find('.//ParamList'):
                    funcBody.append(func.find('.//ParamList'))
                for var in funcBody.findall(".//Decl"):
                    # single variable Decl
                    if var.get('uid').split(',')[0].strip()==varName.strip():
                        # print('============ var '+varName+' found')
                        init='unitilialized'
                        if len(var)==2:
                            # print('declaration and initialization')
                            size = self.declareRecursive(var[0])
                            init = self.initilizieRecursive(var[1])
                        elif len(var)==1:
                            #print('only declerations')
                            size = self.declareRecursive(var[0])
                        else:
                            print('unexpected number of chiled')
                            exit(1)
                        # check for unknow sizes and dynamic allocations
                        if size.find('unkown')!=-1:
                            print('Error: Unable to determine the array size ('+varName.strip()+')')
                            exit(-1)
                        if size.find('dynamic')!=-1:
                            if DEBUG>1:
                                print('dynamic array detected ('+varName.strip()+')')
                            #exit(-1)
                            # find all assignment expressions and look for allocations
                            # ignore C++ new statements for now
                            #for assignm in funcBody.findall(".//Assignment"):
                                #if assignm[0].get('uid').strip()==varName.strip():
                                    #allocationSize = assignmentRecursive(assignm)
                        #print('var('+varName+')-> size='+size+' '+'('+init+')')
                        if DEBUG>2:
                            print size
                        return size
        exit(-1)

    def var_copy_showAll(self):
        # print detected copy statements to stdout
        for i in self.oacc_copys:
            print i

    def var_copy_genCode(self):
        # generate proper code for all the copy expressions
        # even generated with data, kernels, or parallel directive
        # and relpace dummy data copy functions with proper allocation and data tansfers
        for i in range(0,len(self.oacc_copys)):
            codeC='' #code for performing copy
            codeM='' #code for performing allocation
            vardeclare=''
            for j in self.oacc_copys[i].split('\n'):
                varname=''
                incom=''
                present='false'
                dim=[]
                type=''
                dname=''
                size=''
                parentFunc=''
                regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*\ ]*)(\")')
                if DEBUG>1:
                    print 'Copy tuple > '+j
                for (a, b, c, d, e) in regex.findall(j):
                    if a=='varname':
                        varname=d
                    elif a=='in':
                        incom=d
                    elif a=='present':
                        present=d
                    elif a.find('dim')!=-1:
                        dim.append(d)
                    elif a=='type':
                        type=d
                    elif a=='dname':
                        dname=d
                    elif a=='size':
                        size=d
                    elif a=='parentFunc':
                        parentFunc=d
                # handle dynamic allocation here
                if size.find('dynamic')!=-1:
                    if size.count('dynamic')!=len(dim):
                        print 'Error: data clause copy statement and the variable dimension are not matched! variable name: '+varname
                        exit(-1)
                    for repa in dim:
                        if repa.find(':')==-1:
                            print 'Error: dynamic array without the length at the data clause!'
                            print '\tvariable name: '+varname
                            print '\trange statement: '+repa
                            exit(-1)
                        size=size.replace('dynamic',repa.split(':')[1]+'+'+repa.split(':')[0])
                # duplication check for declaration and allocation
                varmapper_allocated_found=0
                for (pp1, pp2) in self.varmapper_allocated:
                    if pp1==parentFunc and pp2==dname:
                        varmapper_allocated_found=1
                        break
                if varmapper_allocated_found==0:
                    # generate declaration
                    vardeclare=vardeclare+type+' '+dname+';\n'
                    vardeclare=vardeclare+'short '+dname+self.suffix_present+'='+('0')+';\n' # for now we assume are variables are present
                    # generate cudaMemalloc
                    if present=='true':
                        codeM=codeM+'if(!'+dname+self.suffix_present+'){\n'
                        codeM=codeM+dname+self.suffix_present+'++;\n'
                        codeM=codeM+'if (getenv("IPMACC_VERBOSE")) printf("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM=codeM+'cudaMalloc((void**)&'+dname+','+size+');\n'
                        codeM=codeM+'}\n'
                    else:
                        codeM=codeM+'if(!'+dname+self.suffix_present+'){\n'
                        codeM=codeM+'if (getenv("IPMACC_VERBOSE")) printf("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM=codeM+'cudaMalloc((void**)&'+dname+','+size+');\n'
                        codeM=codeM+'}\n'
                    self.varmapper_allocated.append((parentFunc,dname))
                # generate cudaMemcpy code
                if incom=='true':
                    codeC=codeC+'if (getenv("IPMACC_VERBOSE")) printf("IPMACC: memory copyin '+varname+'\\n");\n'
                    codeC=codeC+'cudaMemcpy('+dname+','+varname+','+size+','+'cudaMemcpyHostToDevice'+');\n'
                elif incom=='false':
                    codeC=codeC+'if (getenv("IPMACC_VERBOSE")) printf("IPMACC: memory copyout '+varname+'\\n");\n'
                    codeC=codeC+'cudaMemcpy('+varname+','+dname+','+size+','+'cudaMemcpyDeviceToHost'+');\n'
                else:
                    # create, present, or deviceptr
                    codeC=''
            self.code_include=self.code_include+vardeclare
            self.code=self.code.replace(self.prefix_dataalloc+str(i)+'();',codeM)
            self.code=self.code.replace(self.prefix_datacp+str(i)+'();',codeC)
    
    def var_copy_assignExpDetail(self):
        # find the type, size, and parentFunction of variables referred in each copy expression
        # and append it to the existing expression
        text = self.var_parseForYacc(self.code)
        #print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        # generate the XML tree
        if DEBUG>2:
           ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        root = tree.getroot()

        for i in range(0,len(self.oacc_copys)):
            #print i
            list=(self.oacc_copys[i]).split('\n')
            self.oacc_copys[i]=''
            for j in range(0,len(list)-1):
                regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*]*)(\")')
                #print 'regex='+regex.findall(list[j])
                for (a, b, c, d, e) in regex.findall(list[j]):
                    if a=='varname':
                        try:
                            # find the `d` variable in the region
                            varNameList=self.oacc_copysVarNams[i]
                            varTypeList=self.oacc_copysVarTyps[i]
                            #print varTypeList[varNameList.index(d)]
                            list[j]=list[j]+' type="'+varTypeList[varNameList.index(d)]+'"'
                        except:
                            print "fatal error! variable "+d+" is undefined!"
                            exit(-1)
                        list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_copysParent[i],d)+'"'
                        list[j]=list[j]+' size="'+self.var_find_size(d,self.oacc_copysParent[i],root)+'"'
                        list[j]=list[j]+' parentFunc="'+self.oacc_copysParent[i]+'"'
            if DEBUG>0:
                print '\n'.join(list[0:len(list)-1])
            self.oacc_copys[i]='\n'.join(list[0:len(list)-1])
            # print self.oacc_copys[i]

    # varmapper fuctions
    # handle the mapping between host and device variables
    def varmapper_getDeviceName_elseCreate(self,function,varname):
        # return the deviceName of varname. if does not exist, create one.
        for (a, b, c) in self.varmapper:
            if a==function and b==varname:
                return c
        dvarname=self.prefix_varmapper+function+'_'+varname
        self.varmapper.append((function, varname, dvarname))
        return dvarname

    def varmapper_getDeviceName(self,function,varname):
        # return the deviceName of varname. if does not exist, create one.
        for (a, b, c) in self.varmapper:
            if a==function and b==varname:
                return c
        return varname
       
    def varmapper_showAll(self):
        # show all (function, hostVariable) -> deviceVariable mappings
        for (a, b, c) in self.varmapper:
            print '('+a+','+b+')->'+c

    # kernel code generators    
    def debug_kernel_genPlainCode(self):
#        try:
        for i in range(0,len(self.oacc_kernels)):
            if DEBUG>1:
                print 'finding the kernel dimension (`for` size)...'
            [iterators, purestring]=self.find_kernel_forSize(self.oacc_kernels[i])
            if DEBUG>1:
                 print 'iterators are '+','.join(iterators)
            self.oacc_kernelsLoopIterators.append(iterators)
            if DEBUG>1:
                print 'loop iterators: '+','.join(iterators)
            if len(purestring)>=2 and purestring[0:2]=='<>':
                purestring=purestring[2:len(purestring)]
            if DEBUG>1:
                print purestring
            forDims=purestring.replace('@','').split('<>')
            forDims.reverse()
            if DEBUG>1:
                print str(len(forDims))+'==> '+' , '.join(forDims)
#            self.oacc_kernels_forDim.append(forDims)
            kernelBody=self.var_kernel_genPlainCode(i, self.oacc_kernels[i], 0, False, len(forDims), forDims)
            [args, declaration]=self.find_kernel_undeclaredVars_and_args(kernelBody, i)
            [kernelPrototype, kernelDecl]=self.construct_kernel(args, declaration, kernelBody, i)
            self.append_kernel_to_code(kernelPrototype, kernelDecl, i, forDims, args)
#        except:
#            print 'exception in debug_kernel_genPlainCode!'
#            print 'dumping the kernelBody:'
#            print kernelBody
#            exit(-1)
    def append_kernel_to_code(self, kerPro, kerDec, kerId, forDims, args):
        self.code=kerPro+self.code+kerDec
        blockDim='256'
        gridDim='('+'*'.join(forDims)+')/256+1'
        callArgs=[]
        for i in args:
            argName=i.split(' ')
            argName=argName[len(argName)-1]
            callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName))
        kernelInvoc=self.prefix_kernel_gen+str(kerId)+'<<<'+gridDim+','+blockDim+'>>>('+(','.join(callArgs))+')'
        kernelInvoc=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel> gridDim: %d\\tblockDim: %d\\n",'+gridDim+','+blockDim+');\n')+kernelInvoc
        self.code=self.code.replace(self.prefix_kernel+str(kerId)+'()',kernelInvoc)

    def pycparser_getAstTree(self,code):
        text='int main(){\n'+code+';\n}'
        #print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        # generate the XML tree
        #ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        root = tree.getroot()
        return root.find(".//FuncDef/Compound")

    def construct_kernel(self, args, decl, kernelB, kernelId):
        code='__global__ void '+self.prefix_kernel_gen+str(kernelId)
        code=code+'('+(','.join(args))+')'
        proto=code+';\n'
        code=code+'{\n'
        code=code+'int '+self.prefix_kernel_uid+'=threadIdx.x+blockIdx.x*blockDim.x;\n'
        code=code+decl
        code=code+kernelB
        code=code+'}\n'

        return [proto, code]

    def oacc_clauseparser_loop_isindependent(self,clause):
        # k=clause.replace('independent','independent()')
        #regex=re.compile(r'([A-Za-z0-9\ ]+)([\(])([A-Za-z0-9\ ]*)([\)])')
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        for it in regex.findall(clause):
            #print ''.join(it).strip()
            #if ''.join(it).strip()=='independent()':
            if it[0].strip()=='independent':
                return True
            elif it[0].strip()=='seq':
                return False
        return False

    def code_gen_reversiFor(self, initial, boundary, increment):
        return 'for('+initial+';'+str(boundary)+';'+str(increment)+')'

    def count_loopIter(self, init, final, operator, steps):
        # initial value of operator
        # final value of operator (in respect to loop condition)
        # operator: the operator of loop iterator increment
        # steps: value of steps for each loop iterator increment
        if operator=='*' or operator=='/':
            return 'log(abs('+final+'-'+init+')'+')'+'/log('+steps+')'
        elif operator=='+' or operator=='-':
            return '(abs('+final+'-'+init+')'+')'+'/('+steps+')'

    def find_kernel_undeclaredVars_and_args(self, kernelBody, kernelId):
        # here we look for variable 
        # and return their declarations, if they are not already declared
        # here, conservatively, we define all variables as the function argument
        root=self.pycparser_getAstTree(kernelBody)
        # first find all the function calls IDs
        allFc=[]
        for fcc in root.findall(".//FuncCall/ID"):
            allFc.append(str(fcc.get('uid')).strip())
        allFc=list(set(allFc))
        if VERBOSE==1:
            print 'kernels region > Function: '+','.join(allFc)
        # second, find all the ID tags
        vars=[]
        for var in root.findall(".//ID"):
            func=True
            try :
                allFc.index(str(var.get('uid')).strip())
            except :
                func=False
            if not func:
                vars.append(str(var.get('uid')).strip())
        vars=list(set(vars))
        if VERBOSE==1:
            print 'kernels region > Variables: '+','.join(vars)
        # third, find undefined variables
        vars.remove(self.prefix_kernel_uid);
        for var in root.findall(".//Decl"):
            try :
                # ignore declared vars
                vars.remove(str(var.get('uid')).strip())
            except :
                # it was a function call, ignore it
                k=True
        if VERBOSE==1:
            print 'kernels region > Undefined variables: '+','.join(vars)
        # fourth, get the type of desired variables
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        kernelLoopIterators=self.oacc_kernelsLoopIterators[kernelId]
        function_args=[]
        for i in range(0,len(vars)):
            # first, ignore iterator variables
            itr=True
            try:
                idx=kernelLoopIterators.index(vars[i])
            except:
                itr=False
            if itr:
                continue
            # second, find the remaining undeclared variables
            try :
                idx=scopeVarsNames.index(vars[i])
                function_args.append(scopeVarsTypes[idx]+' '+scopeVarsNames[idx])
            except:
                print 'WARNING: Could not determine the type of variable used in the kernel: '+vars[i]
                print '\tignoring undefined variable, maybe a macro solves proble!'
                #exit (-1)
        if VERBOSE==1:
            print 'kernels regions > kernel arguments: '+','.join(function_args)
        # construct declaration
        code=''
        #code=';\n'.join(function_args)+';\n'
        for i in kernelLoopIterators:
            code=code+'int '+i+';\n'
        return [function_args, code]
#        return '// declarations\n'

    def find_kernel_forSize(self, root):
        iterator=[]
        size=''
        forSize=[]
        for ch in root:
            [it, t]=self.find_kernel_forSize(ch)
            if t!='':
                forSize.append(t)
            if len(it)>0:
                iterator=iterator+it
        if len(forSize)>0:
            if len(forSize)>1:
                for g in forSize:
                    if g[0]=='@':
                        size=size+g[1:len(g)]+','
                    else:
                        size=size+g+','
                size='<>max('+size[0:len(size)-1]+')'
            else:
                size=('' if (forSize[0][0]=='<' and forSize[0][1]=='>') else '<>')+forSize[0]
        if root.tag=='for' and root.attrib['independent']=='true':
            # append the for size
            iterator=iterator+[root.attrib.get('iterator')]
            return [iterator, '@'+self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'))+size]
        return [iterator, size]

    def tag_indepLoops(self, root, independent):
        # get kernel and go through it to find independent loops
        if root.tag=='pragma':
            if root.attrib.get('directive')=='kernels':
                for ch in root:
                    self.tag_indepLoops( ch, False)
            elif root.attrib.get('directive')=='loop':
                indep=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                for ch in root:
                    self.tag_indepLoops(ch, indep)
            else:
                print('Invalid: '+root.attrib.get('directive')+' directive in region!')
                exit(-1)
        elif root.tag=='for':
            if independent:
                root.attrib['independent']='true'
                for ch in root:
                    self.tag_indepLoops(ch, False)
            else :
                root.attrib['independent']='false'
                # go through childs
                for ch in root:
                    self.tag_indepLoops(ch, False)

    def var_kernel_genPlainCode(self, id, root, indent, independent, nested, forDims):
        code=''
        #print root.tag
        try:
            if root.tag=='pragma':
                if root.attrib.get('directive')=='kernels':
                    #code=code+'void prototype'+str(id)+'(){\n'
                    #code=code+'int '+self.prefix_kernel_uid+'=threadIdx.x+blockIdx.x*blockDim.x;\n'
                    code=code+'{\n'
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, indent+1, False, nested, forDims)
                    code=code+'}\n'
                elif root.attrib.get('directive')=='loop':
                    indep=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                    for ch in root:
                        #print str(indep)
                        code=code+self.var_kernel_genPlainCode(id, ch, indent+1, indep, nested, forDims)
                else:
                    print('Invalid: '+root.attrib.get('directive')+' directive in region!')
                    exit(-1)
            elif root.tag=='for':
                if root.attrib['independent']=='true': #independent:
                    # generate indexing
                    if nested==0:
                        # fatal error
                        print 'Internal error: Nesting out of control!'
                        exit(-1)
                    if nested==1:
                        # last-level
                        iteratorVal=self.prefix_kernel_uid+'%('+forDims[nested-1]+');'
                    else:
                        # upper levels
                        iteratorVal=self.prefix_kernel_uid+'/('+'*'.join(forDims[0:nested-1])+');'
                    code=code+root.attrib.get('iterator')+'='+iteratorVal+'\n'
                    # generate if statement
                    code=code+'if('+root.attrib.get('boundary')+')\n'
                    # go through childs
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, indent+1, False, nested-1, forDims)
                    # terminate if statement
                    code=code+'\n'
                else :
                    # generate `for` statement
                    code=code+str('\t'*indent)+self.code_gen_reversiFor(root.attrib.get('initial'),root.attrib.get('boundary'),root.attrib.get('increment'))+'\n'
                    # go through childs
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, indent+1, False, nested-1, forDims)
                    # terminate for statement
                    #code=code+root.tag+'\n'
            elif root.tag=='c':
                code=code+root.text.strip()+'\n'
        except:
            print 'exception! dumping the code:\n'+self.code+code
            exit(-1)
        return code

# check for codegen options
parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to output CU file", metavar="FILE", default="")
(options, args) = parser.parse_args()

if options.filename=="":
    parser.print_help()
    exit(-1)
else:
    print 'The output file is : '+options.filename




# read the input XML which is validated by parser
tree = ET.parse('__inter.xml')
root = tree.getroot()

# create a code generator module
k = codegen()

# prepare the destination code by parsing the XML tree
k.code_descendentRetrieve(root,0)
k.code_kernelDump(0);

# proper dumps
#k.code_descendentDump(sys.stdout)
#k.code_kernelPrint(0)
#k.code_kernelDump(0)

# duty: process the intermediate-generated C code and generate kernels, data copies, and ...
# wrap the input C file to suit for YACC
# parse the wrapped C file
# print the type of variables used in the kernel
# k.var_findKernelParents()
k.astCalcRoot()
k.var_kernel_parentsFind()
k.var_copy_parentsFind()
# find the implicit copies
#k.var_copy_varSizeFind()
k.var_copy_assignExpDetail()
k.var_copy_genCode()
#k.var_copy_showAll()
#k.varmapper_showAll()


#k.code_descendentDump('reverse.cu')
#try:
k.debug_kernel_genPlainCode()
#except:
    #print 'exception!'


# prepare to write the code to output
k.code_descendentDump(options.filename)

print "code geneneration completed!"

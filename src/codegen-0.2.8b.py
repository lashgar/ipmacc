import sys
import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
#from termcolor import colored
import os

sys.path.extend(['.', '..', './pycparser/'])
from pycparser import c_parser, c_ast
from utils_clause import clauseDecomposer,clauseDecomposer_break

from subprocess import call, Popen, PIPE
import tempfile

from optparse import OptionParser

# Operation control
ENABLE_INDENT=True
CLEARXML=True
VERBOSE=0
ERRORDUMP=True

# Debugging level control
DEBUG=0
DEBUGCP=0
DEBUGCPARSER=0
DEBUGVAR=False
DEBUGLD=False  # loop detector
DEBUGPRIVRED=False
DEBUGSTMBRK=False

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
    def __init__(self, target, fname=None, foname=None):
        self.oacc_kernelId=0     # number of kernels which are replaced by function calls
        self.oacc_kernels=[]     # array of kernels' roots (each element of array is ElementTree)
        self.oacc_kernelsParent=[]   # array of functions name, indicating which function is the parent of kernel (associated with each elemnt in self.oacc_kernels)
        self.oacc_kernelsVarNams=[] # list of array of variables defined in the kernels' call scope
        self.oacc_kernelsVarTyps=[] # list of array of type of variables defined in the kernels' call scope
        self.oacc_kernelsLoopIteratorsPar=[]   # list of array of iterators of independent/parallel loops
        self.oacc_kernelsLoopIteratorsSeq=[]   # list of array of iterators of sequential loop
        self.oacc_kernelsAutomaPtrs=[]  # per kernel list of variables defined as deviceptr in the respective kernels or data region (no action)
        self.oacc_kernelsManualPtrs=[]  # per kernel list of variables defined explicitly to be copied in, copied out, or allocated in the respective kernels or data region 
        self.oacc_kernelsImplicit=[] # implicit copies corresponding to this kernel
        self.oacc_kernelsReductions=[] # per kernel list of variable to be reduced (used for copy-in copy-out)
        self.oacc_kernelsPrivatizin=[] # per kernel list of variable to be privated (used for copy-in copy-out)
        self.oacc_loopReductions=[] # per call list of variable to be reduced 
        self.oacc_loopPrivatizin=[] # per call list of variable to be privated 
        self.oacc_scopeAutomaPtr='' # carry the variables which are deviceptrs across the current data (not kernels) region scope
        self.oacc_scopeManualPtr='' # carry the variables which are declared explicitly for copy or allocate in current data (not kernels) region scope

        self.oacc_copyId=0  # number of copys which are replaced by function calls
        self.oacc_copys=[]  # array of copys' expression (each element is string)
        self.oacc_copysParent=[]   # array of functions name, indicating the function which is the parent of copy (associated with each elemnt in self.oacc_copys)
        self.oacc_copysVarNams=[] # list of array of variables defined in the copys' call scope
        self.oacc_copysVarTyps=[] # list of array of type of variables defined in the copys' call scope
        
        self.code='' # intermediate generated C code
        self.code_include='#include <stdlib.h>\n#include <stdio.h>\n#include <assert.h>\nvoid ipmacc_prompt(char *s){\nif (getenv("IPMACC_VERBOSE"))\nprintf("%s",s);\n}\n' # .h code including variable decleration and function prototypes
        self.code_include+='#define IPMACC_MAX1(A)   (A)\n'
        self.code_include+='#define IPMACC_MAX2(A,B) (A>B?A:B)\n'
        self.code_include+='#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))\n'

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
        self.prefix_dataimpli='__ungenerated_implicit_data'
        self.prefix_kernel_uid='__kernel_getuid'
        self.prefix_kernel_reduction_shmem='__kernel_reduction_shmem_'
        self.prefix_kernel_reduction_region='__kernel_reduction_region_'
        self.prefix_kernel_privred_region='__kernel_privred_region_'
        self.prefix_kernel_reduction_iterator='__kernel_reduction_iterator'
        self.prefix_kernel_reduction_lock='__ipmacc_reduction_lock_'
        #self.blockDim='256'
        self.blockDim_cuda='256'
        self.blockDim_opencl='256'

        # ast tree
        self.astRoot=0
    
        # codegeneration control
        self.target_platform = ('CUDA' if target=='nvcuda' else 'OPENCL') # alternatives are 'CUDA' 'OPENCL'

    # auxilary functions
    # - replace 1 from the end of string
    def replace_last(self, source_string, replace_what, replace_with):
        head, sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def acc_detected(self):
        return len(self.oacc_kernels)>0

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
        #regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        #for i in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            if DEBUGVAR:
                print 'name-input pair: '+i0+'-'+i3
            if str(i0).strip()==type:
                for j in str(i3).split(','):
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

    def varname_extractor(self,statement):
        vname=[]
        regex=re.compile(r'(varname=")([A-Za-z0-9_]*)(")')
        for i in regex.findall(statement):
            #print i[1]
            vname.append(i[1])
        return ' '.join(vname)
            
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
        #for i in regex.findall(clause):
        for [i0, i1] in clauseDecomposer_break(clause):
            if str(i0).strip()==type:
                return True
        return False

    def oacc_clauseparser_deviceptr(self,clause):
        # parse openacc clause and return '\n' delimited list of deviceptr variables, if exists
        code=''
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        #for i in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            if str(i0).strip()=='deviceptr':
                try:
                    return i3.strip().replace(',',' ')
                except:
                    print 'error: expecting argument (list of variables) for the `deviceptr` caluse'
                    exit(-1)
        return ''
    def oacc_clauseparser_if(self,clause):
        # parse openacc `if` and return condition 
        code=''
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        #for i in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            if str(i0).strip()=='if':
                try:
                    return i3.strip()
                except:
                    print 'error: expecting argument (condition) for the `if` caluse'
                    exit(-1)
        return ''

    # target platform code generators
    def codegen_includeHeaders(self):
        if self.target_platform=='CUDA':
            return self.includeHeaders_cuda()
        elif self.target_platform=='OPENCL':
            return self.includeHeaders_opencl()
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_syncDevice(self):
        if self.target_platform=='CUDA':
            return self.syncDevice_cuda()
        elif self.target_platform=='OPENCL':
            return self.syncDevice_opencl()
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_openCondition(self,cond):
        if self.target_platform=='CUDA':
            return self.openCondition_cuda(cond)
        elif self.target_platform=='OPENCL':
            return self.openCondition_opencl(cond)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_closeCondition(self,cond):
        if self.target_platform=='CUDA':
            return self.closeCondition_cuda(cond)
        elif self.target_platform=='OPENCL':
            return self.closeCondition_opencl(cond)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_appendKernelToCode(self, kerPro, kerDec, kerId, forDims, args):
        if self.target_platform=='CUDA':
            self.appendKernelToCode_cuda(kerPro, kerDec, kerId, forDims, args)
        elif self.target_platform=='OPENCL':
            self.appendKernelToCode_opencl(kerPro, kerDec, kerId, forDims, args)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_reduceVariable(self, var, type, op, ctasize):
        if self.target_platform=='CUDA':
            return self.reduceVariable_cuda(var, type, op, ctasize)
        elif self.target_platform=='OPENCL':
            return self.reduceVariable_opencl(var, type, op, ctasize)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_constructKernel(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims):
        if self.target_platform=='CUDA':
            return self.constructKernel_cuda(args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims)
        elif self.target_platform=='OPENCL':
            return self.constructKernel_opencl(args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_memAlloc(self, var, size):
        if self.target_platform=='CUDA':
            return self.memAlloc_cuda(var, size)
        elif self.target_platform=='OPENCL':
            return self.memAlloc_opencl(var, size)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_memCpy(self, des, src, size, type):
        if self.target_platform=='CUDA':
            return self.memCpy_cuda(des, src, size, type)
        elif self.target_platform=='OPENCL':
            return self.memCpy_opencl(des, src, size, type)
        else:
            print 'error: unimplemented platform'
            exit(-1)
    def codegen_devPtrDeclare(self, type, name, sccopy):
        # sccopy stands for scalar explicit copy
        if self.target_platform=='CUDA':
            return self.devPtrDeclare_cuda(type, name, sccopy)
        elif self.target_platform=='OPENCL':
            return self.devPtrDeclare_opencl(type, name, sccopy)
        else:
            print 'error: unimplemented platform'
            exit(-1)

    # cuda platform
    def includeHeaders_cuda(self):
        self.code_include+='#include <cuda.h>\n'
    def initDevice_cuda(self):
        return ''
    def syncDevice_cuda(self):
        return 'cudaDeviceSynchronize();\n'
    def openCondition_cuda(self,cond):
        return 'if('+cond+'){\n'
    def closeCondition_cuda(self,cond):
        return '}\n'
    def appendKernelToCode_cuda(self, kerPro, kerDec, kerId, forDims, args):
        self.code=kerPro+self.code+kerDec
        blockDim=self.blockDim_cuda
        #gridDim='('+'*'.join(forDims)+')/256+1'
        gridDim='('+forDims+')/'+blockDim+'+1'
        callArgs=[]
        for i in args:
            argName=i.split(' ')
            argName=argName[len(argName)-1]
            argName=argName.replace('__ipmacc_scalar','')
            callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName))
        kernelInvoc='\n/*kernel call statement*/\n'
        kernelInvoc+=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel> gridDim: %d\\tblockDim: %d\\n",'+gridDim+','+blockDim+');\n')
        kernelInvoc+=self.prefix_kernel_gen+str(kerId)+'<<<'+gridDim+','+blockDim+'>>>('+(','.join(callArgs))+');'
        kernelInvoc+='\n/*^D kernel call statement*/\n'
        self.code=self.code.replace(self.prefix_kernel+str(kerId)+'();',kernelInvoc)
    def reduceVariable_cuda(self, var, type, op, ctasize):
        arrname=self.prefix_kernel_reduction_shmem+type
        iterator=self.prefix_kernel_reduction_iterator
        code ='\n/* reduction on '+var+' */\n'
        code+='__syncthreads();\n'
        code+=arrname+'[threadIdx.x]='+var+';\n';
        code+='__syncthreads();\n'
        code+='for('+iterator+'='+ctasize+'; '+iterator+'>1; '+iterator+'='+iterator+'/2){\n'
        code+='if(threadIdx.x<'+iterator+' && threadIdx.x>='+iterator+'/2){\n'
        des=arrname+'[threadIdx.x-('+iterator+'/2)]'
        src=arrname+'[threadIdx.x]'
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+='}\n'
        code+='__syncthreads();\n'
        code+='}\n'
        code+='}// the end of '+var+' scope\n'
        # this reduction works for most devices, but can be implemented efficienctly considering device specific atomic operations
        #code+='/*atomicAdd('+var+','+var+'[0]+'+arrname+'[0]);\n\n*/'
        self.code_include+='__device__ unsigned long long int '+self.prefix_kernel_reduction_lock+var+'=0u;\n'
        code+='if(threadIdx.x==0){\n'
        code+='while (atomicCAS(&'+self.prefix_kernel_reduction_lock+var+', 0u, 1u)==1u){\n'
        code+='};\n'
        code+='//start global critical secion\n'
        des=var+'[0]'
        src=arrname+'[0]'
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+=self.prefix_kernel_reduction_lock+var+'=0u;\n'
        code+='//^D end global critical secion\n'
        code+='}\n'
        return code
    def constructKernel_cuda(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims):
        code='__global__ void '+self.prefix_kernel_gen+str(kernelId)
        code=code+'('+(','.join(args))+')'
        proto=code+';\n'
        code+='{\n'
        code+='int '+self.prefix_kernel_uid+'=threadIdx.x+blockIdx.x*blockDim.x;\n'
        # fetch __ipmacc_scalar into register
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                type=sc.replace(vname,'').replace('*','')
                code+=type+' '+vname.replace('__ipmacc_scalar','')+' = '+vname+'[0];\n'
        #code+='if('+self.prefix_kernel_uid+'>='+forDims+'){\nreturn;\n}\n'
        if len(reduinfo)>0:
            # 1) serve privates
            pfreelist=[]
            for [v, i, o, a, t] in privinfo:
                fcall=self.prefix_kernel_privred_region+str(a)+'();'
                scp='{//this will be closed at the end of '+v+' scope \n'
                kernelB=kernelB.replace(fcall,scp+t+' '+v+'='+i+';\n'+fcall)
                pfreelist.append(a)
            for ids in pfreelist:
                fcall=self.prefix_kernel_privred_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'');
            # 2) serve reductions
            decl+='int '+self.prefix_kernel_reduction_iterator+'=0;\n'
            types=[] # types to reserve space for fast shared-memory reductions
            rfreelist=[] #remove reduction calls
            reduinfo.reverse()
            for [v, i, o, a, t] in reduinfo:
                fcall=self.prefix_kernel_reduction_region+str(a)+'();'
                # 2) 1) append proper reduction code for this variable
                kernelB=kernelB.replace(fcall,self.codegen_reduceVariable(v,t,o,ctasize)+fcall)
                types.append(t)
                rfreelist.append(a)
            reduinfo.reverse()
            # 2) 2) allocate shared memory reduction array
            types=list(set(types))
            for t in types:
                code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+t+'['+ctasize+'];\n'
            rfreelist=list(set(rfreelist))
            # 2) 3) free remaining fcalls
            for ids in rfreelist:
                fcall=self.prefix_kernel_reduction_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'')
        code=code+decl
        code=code+kernelB
        code=code+'}\n'
        return [proto, code]
    def memAlloc_cuda(self, var, size):
        codeM='cudaMalloc((void**)&'+var+','+size+');\n'
        return codeM
    def memCpy_cuda(self, des, src, size, type):
        codeC='cudaMemcpy('+des+','+src+','+size+','+('cudaMemcpyHostToDevice' if type=='in' else 'cudaMemcpyDeviceToHost')+');\n'
        return codeC
    def devPtrDeclare_cuda(self, type, name, sccopy):
        return type+('* ' if sccopy else ' ')+name+';\n'

    # opencl platform
    def includeHeaders_opencl(self):
        self.code_include+='#include <CL/cl.h>\n'
        self.code_include+=self.initDeviceVar_opencl()
    def initDeviceVar_opencl(self):
        codeC=''
        codeC+='extern cl_int __ipmacc_clerr ;\n'
        codeC+='extern cl_context __ipmacc_clctx ;\n'
        codeC+='extern size_t __ipmacc_parmsz;\n'
        codeC+='extern cl_device_id* __ipmacc_cldevs;\n'
        codeC+='extern cl_command_queue __ipmacc_command_queue;\n'
        return codeC
    def syncDevice_opencl(self):
        return 'clFlush(__ipmacc_command_queue);\n'
    def openCondition_opencl(self,cond):
        return 'if('+cond+'){\n'
    def closeCondition_opencl(self,cond):
        return '}\n'
    def appendKernelToCode_opencl(self, kerPro, kerDec, kerId, forDims, args):
        #self.code=kerPro+self.code+kerDec
        blockDim=self.blockDim_opencl
        #gridDim='('+'*'.join(forDims)+')/256+1'
        gridDim='(('+forDims+'/'+blockDim+')+1)*'+blockDim
        #callArgs=[]
        #for i in args:
        #    argName=i.split(' ')
        #    argName=argName[len(argName)-1]
        #    callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName))
        # remove undefined declaration from __kernel in three steps: 1) append kernel to code, 2) parse it using cpp, 3) extract the kernel back
        cleanKerDec=''
        for [tp,incstm] in self.code_getAssignments(self.var_parseForYacc(self.code+'\n'+kerDec),['fcn']):
            if incstm.strip()[0:8]=='__kernel':
                cleanKerDec=incstm
                break
        if cleanKerDec=='':
            print 'Fatal internal error! enable to retrieve back the kernel!'
            exit(-1)
        #cleanKerDec=statmnts+kerDec
        cleanKerDec=cleanKerDec.replace('"','\"')
        cleanKerDec=cleanKerDec.replace('\n','\\n')
        kernelInvoc='\n/*kernel call statement*/\n'
        kernelInvoc+='const char* kernelSource ="'+cleanKerDec+'";\n'
        kernelInvoc+='cl_program __ipmacc_clpgm;\n'
        kernelInvoc+='__ipmacc_clpgm=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource, NULL, &__ipmacc_clerr);\n'
        kernelInvoc+=self.checkCallError_opencl('clCreateProgramWithSource')
        kernelInvoc+='char __ipmacc_clcompileflags[128];\n'
        kernelInvoc+='sprintf(__ipmacc_clcompileflags, " ");\n'
        #kernelInvoc+='sprintf(__ipmacc_clcompileflags, "-cl-mad-enable");\n'
        kernelInvoc+='clBuildProgram(__ipmacc_clpgm, 0, NULL, __ipmacc_clcompileflags, NULL, NULL);\n'
        kernelInvoc+=self.checkCallError_opencl('clBuildProgram')
        kernelInvoc+='cl_kernel __ipmacc_clkern = clCreateKernel(__ipmacc_clpgm, "'+self.prefix_kernel_gen+str(kerId)+'", &__ipmacc_clerr);\n'
        kernelInvoc+=self.checkCallError_opencl('clCreateKernel')
        for j in range(0,len(args)):
            pointer=(args[j].find('*')!=-1)
            argName=args[j].split(' ')[-1].replace('__ipmacc_scalar','')
            argType=' '.join(args[j].split(' ')[0:-1])
            #callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName))
            dname=self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName)
            if pointer:
                kernelInvoc+='__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern, '+str(j)+', sizeof(cl_mem), (void *)&'+dname+');\n'
            else:
                kernelInvoc+='__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern, '+str(j)+', sizeof('+argType.replace('*','')+'), (void *)&'+dname+');\n'
            kernelInvoc+=self.checkCallError_opencl('clSetKernelArg')
        kernelInvoc+=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel> gridDim: %d\\tblockDim: %d\\n",'+gridDim+','+blockDim+');\n')
        kernelInvoc+='size_t global_item_size = '+gridDim+';\n'
        kernelInvoc+='size_t local_item_size = '+blockDim+';\n'
        kernelInvoc+='__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_command_queue, __ipmacc_clkern, 1, NULL,\n &global_item_size, &local_item_size, 0, NULL, NULL);\n'
        kernelInvoc+=self.checkCallError_opencl('clEnqueueNDRangeKernel')
        #kernelInvoc+=self.prefix_kernel_gen+str(kerId)+'<<<'+gridDim+','+blockDim+'>>>('+(','.join(callArgs))+');'
        kernelInvoc+='\n/*^D kernel call statement*/\n'
        self.code=self.code.replace(self.prefix_kernel+str(kerId)+'();',kernelInvoc)
    def reduceVariable_opencl(self, var, type, op, ctasize):
        arrname=self.prefix_kernel_reduction_shmem+type
        iterator=self.prefix_kernel_reduction_iterator
        code ='\n/* reduction on '+var+' */\n'
        code+='barrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n'
        code+=arrname+'[get_local_id(0)]='+var+';\n';
        code+='barrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n'
        code+='for('+iterator+'='+ctasize+'; '+iterator+'>1; '+iterator+'='+iterator+'/2){\n'
        code+='if(get_local_id(0)<'+iterator+' && get_local_id(0)>='+iterator+'/2){\n'
        des=arrname+'[get_local_id(0)-('+iterator+'/2)]'
        src=arrname+'[get_local_id(0)]'
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+='}\n'
        code+='barrier(CLK_LOCAL_MEM_FENCE | CLK_GLOBAL_MEM_FENCE);\n'
        code+='}\n'
        code+='}// the end of '+var+' scope\n'
        # this reduction works for most devices, but can be implemented efficienctly considering device specific atomic operations
        #code+='/*atomicAdd('+var+','+var+'[0]+'+arrname+'[0]);\n\n*/'
        self.code_include+='__global unsigned long long int '+self.prefix_kernel_reduction_lock+var+'=0u;\n'
        code+='if(threadIdx.x==0){\n'
        code+='while (atomicCAS(&'+self.prefix_kernel_reduction_lock+var+', 0u, 1u)==1u){\n'
        code+='};\n'
        code+='//start global critical secion\n'
        des=var+'[0]'
        src=arrname+'[0]'
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+=self.prefix_kernel_reduction_lock+var+'=0u;\n'
        code+='//^D end global critical secion\n'
        code+='}\n'
        return code
    def constructKernel_opencl(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims):
        code='__kernel void '+self.prefix_kernel_gen+str(kernelId)
        suff_args=[]
        for idx in range(0,len(args)):
            sc=args[idx]
            if sc.count('*')!=0:
                suff_args.append('__global '+sc)
            else:
                suff_args.append(sc)
        code+='('+','.join(suff_args)+')'
        proto=code+';\n'
        code+='{\n'
        code+='int '+self.prefix_kernel_uid+'=get_global_id(0);\n'
        # fetch __ipmacc_scalar into register
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                type=sc.replace(vname,'').replace('*','')
                code+=type+' '+vname.replace('__ipmacc_scalar','')+' = '+vname+'[0];\n'
        #code+='if('+self.prefix_kernel_uid+'>='+forDims+'){\nreturn;\n}\n'
        if len(reduinfo)>0:
            # 1) serve privates
            pfreelist=[]
            for [v, i, o, a, t] in privinfo:
                fcall=self.prefix_kernel_privred_region+str(a)+'();'
                scp='{//this will be closed at the end of '+v+' scope \n'
                kernelB=kernelB.replace(fcall,scp+t+' '+v+'='+i+';\n'+fcall)
                pfreelist.append(a)
            for ids in pfreelist:
                fcall=self.prefix_kernel_privred_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'');
            # 2) serve reductions
            decl+='int '+self.prefix_kernel_reduction_iterator+'=0;\n'
            types=[] # types to reserve space for fast shared-memory reductions
            rfreelist=[] #remove reduction calls
            reduinfo.reverse()
            for [v, i, o, a, t] in reduinfo:
                fcall=self.prefix_kernel_reduction_region+str(a)+'();'
                # 2) 1) append proper reduction code for this variable
                kernelB=kernelB.replace(fcall,self.codegen_reduceVariable(v,t,o,ctasize)+fcall)
                types.append(t)
                rfreelist.append(a)
            reduinfo.reverse()
            # 2) 2) allocate shared memory reduction array
            types=list(set(types))
            for t in types:
                code=code+'__local '+t+' '+self.prefix_kernel_reduction_shmem+t+'['+ctasize+'];\n'
            rfreelist=list(set(rfreelist))
            # 2) 3) free remaining fcalls
            for ids in rfreelist:
                fcall=self.prefix_kernel_reduction_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'')
        code=code+decl
        code=code+kernelB
        code=code+'}\n'
        return [proto, code]
    def memAlloc_opencl(self, var, size):
        codeM=var+' = clCreateBuffer(__ipmacc_clctx, CL_MEM_READ_WRITE, '+size+', NULL, &__ipmacc_clerr);\n'
        codeM+=self.checkCallError_opencl('clCreateBuffer')
        return codeM
    def memCpy_opencl(self, des, src, size, type):
        if type=='in':
            codeC='clEnqueueWriteBuffer(__ipmacc_command_queue, '+des+', CL_TRUE, 0, '+size+','+src+', 0, NULL, NULL);\n'
            codeC+=self.checkCallError_opencl('clEnqueueWriteBuffer')
        else:
            codeC='clEnqueueReadBuffer(__ipmacc_command_queue, '+src+', CL_TRUE, 0, '+size+','+des+', 0, NULL, NULL);\n'
            codeC+=self.checkCallError_opencl('clEnqueueReadBuffer')
        return codeC
    def devPtrDeclare_opencl(self, type, name, sccopy):
        #return 'cl_mem'+('* ' if sccopy else ' ')+name+';\n'
        return 'cl_mem '+name+';\n'
    def checkCallError_opencl(self,fcn):
        code ='if(__ipmacc_clerr!=CL_SUCCESS){\n'
        code+='printf("OpenCL Runtime Error in '+fcn+'! id: %d\\n",__ipmacc_clerr);\n'
        code+='exit(-1);\n'
        code+='}\n'
        return code
    # Marking for final replacement
    def mark_implicitcopy(self,inout,kid):
        return self.prefix_dataimpli+inout+str(kid)+'();'

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
            if DEBUGVAR:
                print 'Kernels data clause: '+expressionIn+'\n'+expressionAlloc+'\n'+expressionOut # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
            # * generate proper code before the kernels region:
            #   - if
            regionCondition=self.oacc_clauseparser_if(str(root.attrib.get('clause')))
            if regionCondition!='':
                self.code=self.code+self.codegen_openCondition(regionCondition)
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
            #   - track automatic vars (deviceptr)
            expressionDeviceptrs=self.oacc_clauseparser_deviceptr(str(root.attrib.get('clause')))
            if expressionDeviceptrs!='' or self.oacc_scopeAutomaPtr!='':
                # append in either case
                if DEBUGVAR:
                    print 'appending automatic vars: '+(expressionDeviceptrs+' '+self.oacc_scopeAutomaPtr).strip().replace(' ',',')
                self.oacc_kernelsAutomaPtrs.append((expressionDeviceptrs+' '+self.oacc_scopeAutomaPtr).strip().replace(' ',','))
            #   - track manual vars (copy in, copy out, and create)
            expressionManualVars=self.varname_extractor(expressionIn+'\n'+expressionOut+'\n'+expressionAlloc)
            if DEBUGVAR:
                print 'Extracted manual variable names > '+expressionManualVars
            if expressionManualVars!='' or self.oacc_scopeManualPtr!='':
                # append in either case
                self.oacc_kernelsManualPtrs.append((expressionManualVars+' '+self.oacc_scopeManualPtr).strip().replace(' ',','))
            #   - speculative implicit memory allocation/transfers
            self.code=self.code+self.mark_implicitcopy('in',self.oacc_kernelId)
            # * generate dummy kernel launch function call
            self.code=self.code+self.prefix_kernel+str(self.oacc_kernelId)+'();'
            self.carry_loopAttr2For(root,False,[],[])
            self.oacc_kernels.append(root)
            # * generate proper code after the kernels region:
            #   - copy, copyout (transfer)
            if expressionOut!='':
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(copyoutId)+'();'
            #   - speculative implicit memory allocation/transfers
            self.code=self.code+self.mark_implicitcopy('out',self.oacc_kernelId)
            #   - async
            if not self.oacc_clauseparser_flags(str(root.attrib.get('clause')),'async'):
                self.code=self.code+self.codegen_syncDevice()
            #   - if
            if regionCondition!='':
                self.code=self.code+self.codegen_closeCondition(regionCondition)
            # * finilize state
            self.oacc_kernelId=self.oacc_kernelId+1
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
            temp_scopeAutoma=''
            temp_scopeManual=''
            if root.tag == 'for':
                self.code=self.code+str('\t'*depth)+'for('+str(root.attrib.get('initial'))+';'+str(root.attrib.get('boundary'))+';'+str(root.attrib.get('increment'))+')'
            elif (root.tag=='pragma' and root.attrib.get('directive')=='data'):
                # parse data clauses and
                [expressionIn, expressionAlloc, expressionOut, copyoutId] = self.oacc_clauseparser_data(str(root.attrib.get('clause')))
                if DEBUGCP>0:
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
                #   - automatic variables [deviceptr] (update deviceptr variable of this scope, if anything is defined)
                temp_scopeAutoma=self.oacc_clauseparser_deviceptr(str(root.attrib.get('clause')))
                if temp_scopeAutoma!='':
                    self.oacc_scopeAutomaPtr=self.oacc_scopeAutomaPtr+temp_scopeAutoma+' '
                #   - manual variables (explicit copies)
                temp_scopeManual=self.varname_extractor(expressionIn+'\n'+expressionOut+'\n'+expressionAlloc)
                # print temp_scopeManual
                if temp_scopeManual!='':
                    self.oacc_scopeManualPtr=self.oacc_scopeManualPtr+temp_scopeManual+' '
            for child in root:
                self.code_descendentRetrieve(child,depth+1)
            # dump pragma copyout transfer after the region
            if (root.tag=='pragma' and root.attrib.get('directive')=='data') and expressionOut!='':
                # dump pragma transfer after region
                self.code=self.code+('\t'*depth)+self.prefix_datacp+str(copyoutId)+'();'
                #   - automatic variables [deviceptr]
                if temp_scopeAutoma!='':
                    # subtract this scope automatic variables
                    self.oacc_scopeAutomaPtr=self.replace_last(self.oacc_scopeAutomaPtr, temp_scopeAutoma+' ', '')
                #   - manual variables
                if temp_scopeManual!='':
                    # subtract this scope manual variables
                    self.oacc_scopeManualPtr=self.replace_last(self.oacc_scopeManualPtr, temp_scopeManual+' ', '')

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
    def code_getAssignments(self,code,specialRet=[]):
        # parse the code and break it into top-level assignments:
        # function declaration, type declaration, prototying,
        statements=[]
        #[sttyp,ststr,start,unknown,inc,defi,typdec]=['udf','',True,False,False,False,False]
        [sttyp,ststr,start,incdef]=['udf','',True,False]
        # sttyp: udf undefined, fcn function, ukw unknown-directive, inc include-directive, def define-directive, typ typedef-or-struct-declaration, 
        openpar=0
        for idx in range(0,len(code)):
            ch=code[idx]
            ststr+=ch
            stmend=False
            # start string control
            if start==True and (ch==' ' or ch=='\n' or ch=='\t'):
                continue
            elif start==True:
                start=False
                # non-whitespace start of statement
                if ch=='#':
                    #print 'given char> '+code[idx+1:idx+20].strip()[0:7]
                    incdef=True
                    if   code[idx+1:idx+20].strip()[0:6]=='define':
                        sttyp='def'
                    elif code[idx+1:idx+20].strip()[0:7]=='include':
                        sttyp='inc'
                    else:
                        sttyp='ukw'
                else:
                    if   code[idx:idx+20].strip()[0:7]=='typedef':
                        sttyp='typ'
                    elif code[idx:idx+20].strip()[0:6]=='struct':
                        sttyp='str'
            # process ch
            if ch=='{':
                openpar+=1
            elif ch=='}':
                openpar-=1
            if (openpar==0 and ch=='}') or (openpar==0 and ch==';') or (incdef and ch=='\n'):
                stmend=True
            # check for type
            if ch=='(' and openpar==0 and sttyp=='udf':
                sttyp='fcn'
            # statement termination check
            if stmend:
                skip=True
                if len(specialRet)==0:
                    skip=False
                else:
                    for itm in specialRet:
                        if sttyp==itm:
                            skip=False
                if not skip:
                    statements.append([sttyp,ststr.strip()])
                [sttyp,ststr,start,incdef]=['udf','',True,False]
        return statements
    #
    # VARIABLE TYPE DETECTOR FUNCTIONS: var_kernel_parentsFind, var_copy_parentsFind, var_findFuncParents, var_parseForYacc,
    def astCalcRoot(self):
        text = self.var_parseForYacc(self.code)
        if DEBUGCPARSER>0:
            print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')

        # generate the XML tree
        if DEBUGCPARSER>0:
            ast.show()
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
                        declP=''
                        for chl in var:
                            declP=tostring(chl)
                            if DEBUGCP>1:
                                print var.get('uid').split(',')[0]+'->'
                                print '\t>'+declP
                            break
                        funcVars.append(var.get('uid').split(',')[0])
                        #funcTyps.append(var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl"))+len(var.findall(".//ArrayDecl")))*'*'))
                        funcTyps.append(var.find('.//IdentifierType').get('uid')+((declP.count("<PtrDecl")+declP.count("<ArrayDecl>"))*'*'))
                        if DEBUGCP>1:
                            #print('< '+var.get('uid')+' > is defined as <'+var.find('.//IdentifierType').get('uid')+((len(var.findall(".//PtrDecl")))*'*')+'>')
                            print('< '+var.get('uid')+' > is defined as <'+var.find('.//IdentifierType').get('uid')+((declP.count("<PtrDecl"))*'*')+'>')
                    
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
        p2 = Popen(["cpp", "-E", "-I"+os.path.dirname(os.path.realpath(__file__))+"/../include/"], stdin=p1.stdout, stdout=PIPE)
        code = p2.communicate()[0]
        os.remove(f.name)
        # 3) remove cpp # in the begining of file
        code=re.sub(r'(#\ ).*.(\n)', '', code)
        code=code.replace("extern \"C\"",'');
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
                            exit(-1)
                        # check for unknow sizes and dynamic allocations
                        if size.find('unkown')!=-1:
                            print('Error: Unable to determine the array size ('+varName.strip()+')')
                            exit(-1)
                        if size.find('dynamic')!=-1:
                            if DEBUGCP>1:
                                print('dynamic array detected ('+varName.strip()+')')
                            #exit(-1)
                            # find all assignment expressions and look for allocations
                            # ignore C++ new statements for now
                            #for assignm in funcBody.findall(".//Assignment"):
                                #if assignm[0].get('uid').strip()==varName.strip():
                                    #allocationSize = assignmentRecursive(assignm)
                        #print('var('+varName+')-> size='+size+' '+'('+init+')')
                        if DEBUGCP>2:
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

        regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\+\^\|\&\(\)\*\ ]*)(\")')
        # explicit memory copies
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
                if DEBUGCP>1:
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
                varmapper_allocated_found=False
                for (pp1, pp2) in self.varmapper_allocated:
                    if pp1==parentFunc and pp2==dname:
                        varmapper_allocated_found=True
                        break
                scalar_copy=(type.count('*')==0)
                if varmapper_allocated_found==False:
                    # generate declaration
                    vardeclare+=self.codegen_devPtrDeclare(type,dname,scalar_copy)
                    vardeclare+='short '+dname+self.suffix_present+'='+('0')+';\n' # for now we assume are variables are present
                    # generate accelerator allocation
                    if present=='true':
                        codeM+='if(!'+dname+self.suffix_present+'){\n'
                        codeM+=dname+self.suffix_present+'++;\n'
                        codeM=codeM+'ipmacc_prompt("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size)
                        codeM+='}\n'
                    else:
                        codeM+='if(!'+dname+self.suffix_present+'){\n'
                        codeM=codeM+'ipmacc_prompt("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size)
                        codeM+='}\n'
                    self.varmapper_allocated.append((parentFunc,dname))
                # generate memory copy code
                if incom=='true':
                    codeC+='ipmacc_prompt("IPMACC: memory copyin '+varname+'\\n");\n'
                    codeC+=self.codegen_memCpy(dname, ('&' if scalar_copy else '')+varname, size, 'in')
                elif incom=='false':
                    codeC+='ipmacc_prompt("IPMACC: memory copyout '+varname+'\\n");\n'
                    codeC+=self.codegen_memCpy(('&' if scalar_copy else '')+varname, dname, size, 'out')
                else:
                    # create, present, or deviceptr
                    codeC=''
            self.code_include=self.code_include+vardeclare
            self.code=self.code.replace(self.prefix_dataalloc+str(i)+'();',codeM)
            self.code=self.code.replace(self.prefix_datacp+str(i)+'();',codeC)

        # implicit/reduction memory copies
        for i in range(0,len(self.oacc_kernelsImplicit)):
            codeCin='' #code for performing copy in
            codeCout='' #code for performing copy in
            codeM='' #code for performing allocation
            vardeclare=''
            if len(self.oacc_kernelsReductions)!=len(self.oacc_kernelsImplicit):
                print 'Fatal internal error!\n'
                exit(-1)
            for j in (self.oacc_kernelsImplicit[i].split('\n')+self.oacc_kernelsReductions[i].split('\n')):
                varname=''
                incom='inout'
                present='false'
                dim=[]
                type=''
                dname=''
                size=''
                parentFunc=''
                reduc=''
#                regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*\ ]*)(\")')
                for (a, b, c, d, e) in regex.findall(j):
                    if a=='varname':
                        varname=d
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
                    elif a=='operat':
                        reduc=d
                if varname=='':
                    # invalid tuple, ignore
                    continue
                if DEBUGCP>1:
                    print 'Copy tuple > '+j
                # handle dynamic allocation here
                if size.find('dynamic')!=-1:
                    if size.count('dynamic')!=len(dim):
                        print 'Error: implicit variable cannot be dynamic array! variable name: '+varname
                        print '\tproblem can be avoided by explicit data clause'
                        exit(-1)
                    for repa in dim:
                        if repa.find(':')==-1:
                            print 'Error: dynamic array without the length at the data clause!'
                            print '\tvariable name: '+varname
                            print '\trange statement: '+repa
                            exit(-1)
                        size=size.replace('dynamic',repa.split(':')[1]+'+'+repa.split(':')[0])
                # duplication check for declaration and allocation
                varmapper_allocated_found=False
                for (pp1, pp2) in self.varmapper_allocated:
                    if pp1==parentFunc and pp2==dname:
                        varmapper_allocated_found=True
                        break
                scalar_copy=(type.count('*')==0)
                if varmapper_allocated_found==False:
                    # generate declaration
                    vardeclare+=self.codegen_devPtrDeclare(type,dname,scalar_copy)
                    vardeclare+='short '+dname+self.suffix_present+'='+('0')+';\n' # for now we assume are variables are present
                    # generate accelerator allocation
                    if present=='true':
                        codeM+='if(!'+dname+self.suffix_present+'){\n'
                        codeM+=dname+self.suffix_present+'++;\n'
                        codeM=codeM+'ipmacc_prompt("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size)
                        codeM+='}\n'
                    else:
                        codeM+='if(!'+dname+self.suffix_present+'){\n'
                        codeM=codeM+'ipmacc_prompt("IPMACC: memory allocation '+dname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size)
                        codeM=codeM+'}\n'
                    self.varmapper_allocated.append((parentFunc,dname))
                # generate memory copy in/out code
                passbyref='' if reduc=='' else '&'
#                if incom=='true':
                codeCin+='ipmacc_prompt("IPMACC: memory copyin '+varname+'\\n");\n'
                codeCin+=self.codegen_memCpy(dname, passbyref+varname, size, 'in')
#                elif incom=='false':
                codeCout+='ipmacc_prompt("IPMACC: memory copyout '+varname+'\\n");\n'
                codeCout+=self.codegen_memCpy(passbyref+varname, dname, size, 'out')
            self.code_include=self.code_include+vardeclare
            self.code=self.code.replace(self.prefix_dataalloc+str(i)+'();',codeM)
            self.code=self.code.replace(self.prefix_dataimpli+'in'+str(i)+'();',codeM+codeCin)
            self.code=self.code.replace(self.prefix_dataimpli+'out'+str(i)+'();',codeCout)
   
    
    def var_copy_assignExpDetail(self):
        # find the type, size, and parentFunction of variables referred in each copy expression
        # and append it to the existing expression
        text = self.var_parseForYacc(self.code)
        #print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        # generate the XML tree
        if DEBUGCP>2:
           ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        root = tree.getroot()

        # explicit memory copies
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
                            #ndim=varTypeList[varNameList.index(d)].count('*')
                            #for it in range(1,ndim+1):
                            #    list[j]=list[j]+' dim'+str(it)+'="'+'NA'+'"'
                        except:
                            print "fatal error! variable "+d+" is undefined!"
                            exit(-1)
                        list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_copysParent[i],d)+'"'
                        list[j]=list[j]+' size="'+self.var_find_size(d,self.oacc_copysParent[i],root)+'"'
                        list[j]=list[j]+' parentFunc="'+self.oacc_copysParent[i]+'"'
            if DEBUGCP>0:
                print '\n'.join(list[0:len(list)-1])
            self.oacc_copys[i]='\n'.join(list[0:len(list)-1])
            # print self.oacc_copys[i]

        # implicit memory copies
        for i in range(0,len(self.oacc_kernelsImplicit)):
            # implicit
            #print i
            list=self.oacc_kernelsImplicit[i]
            self.oacc_kernelsImplicit[i]=''
            for j in range(0,len(list)):
                if list[j].strip()=='':
                    list[j]=''
                    continue
                d=list[j]
                list[j]='varname="'+d+'"'
                #regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*]*)(\")')
                #print 'regex='+regex.findall(list[j])
                try:
                    # find the `d` variable in the region
                    varNameList=self.oacc_kernelsVarNams[i]
                    varTypeList=self.oacc_kernelsVarTyps[i]
                    #print varTypeList[varNameList.index(d)]
                    list[j]=list[j]+' type="'+varTypeList[varNameList.index(d)]+'"'
                except:
                    print "fatal error! variable "+d+" is undefined!"
                    exit(-1)
                list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_kernelsParent[i],d)+'"'
                list[j]=list[j]+' size="'+self.var_find_size(d,self.oacc_kernelsParent[i],root)+'"'
                list[j]=list[j]+' parentFunc="'+self.oacc_kernelsParent[i]+'"'
            if DEBUGCP>0:
                print 'implicit copies for kernel'+str(i)+'> '+('\n'.join(list))
            self.oacc_kernelsImplicit[i]='\n'.join(list)
            # print self.oacc_copys[i]

        # reduction memory copies
        for i in range(0,len(self.oacc_kernelsReductions)):
            list=self.oacc_kernelsReductions[i]
            self.oacc_kernelsReductions[i]=''
            for j in range(0,len(list)):
                [vnm, init, op, asi, tp]=list[j]
                if vnm.strip()=='':
                    list[j]=''
                    continue
                list[j]='varname="'+vnm+'"'
                list[j]+=' initia="'+init+'"'
                list[j]+=' operat="'+op+'"'
                list[j]+=' assign="'+str(asi)+'"'
#                list[j]+=' predty="'+tp+'"'
                #regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*]*)(\")')
                #print 'regex='+regex.findall(list[j])
                try:
                    # find the `vnm` variable in the region
                    varNameList=self.oacc_kernelsVarNams[i]
                    varTypeList=self.oacc_kernelsVarTyps[i]
                    #print varTypeList[varNameList.index(vnm)]
                    list[j]=list[j]+' type="'+varTypeList[varNameList.index(vnm)]+'*"'
                except:
                    print "fatal error! variable "+vnm+" is undefined!"
                    exit(-1)
                list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_kernelsParent[i],vnm)+'"'
                list[j]=list[j]+' size="'+self.var_find_size(vnm,self.oacc_kernelsParent[i],root)+'"'
                list[j]=list[j]+' parentFunc="'+self.oacc_kernelsParent[i]+'"'
            if DEBUGPRIVRED>0:
                print 'reduction copies for kernel'+str(i)+'> '+('\n'.join(list))
            self.oacc_kernelsReductions[i]='\n'.join(list)

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


    def pycparser_getAstTree(self,code):
        text=self.code
        text=text+'int __ipmacc_main(){\n'+code+';\n}'
        text=self.var_parseForYacc(text)
        if DEBUGCPARSER:
            print text
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        # generate the XML tree
        if DEBUGCPARSER:
            ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        root = tree.getroot()
#        return root.find(".//FuncDef/Compound")
        for ch in root.findall(".//FuncDef"):
            #print ch
            if ch.find('Decl').get('uid').strip()=='__ipmacc_main':
                return ch.find('Compound')
        print "Fatal error!"
        exit(-1)
#    def pycparser_getAstTree(self,code):
#        text='int main(){\n'+code+';\n}'
#        if DEBUGCPARSER>0:
#            print text
#        # create a pycparser
#        parser = c_parser.CParser()
#        # handle the dump
#        f = open('./__ipmacc_c_code_unable_to_parse.c','w')
#        old_stdout = sys.stdout
#        sys.stdout = f
#        print text
#        sys.stdout = old_stdout
#        f.close()
#        sys.stdout = old_stdout
#        if ENABLE_INDENT==True:
#            Popen(["indent", filename])

    #
    # VARIABLE TYPE DETECTOR FUNCTIONS: var_kernel_parentsFind, var_copy_parentsFind, var_findFuncParents, var_parseForYacc,
    def astCalcRoot(self):
        text = self.var_parseForYacc(self.code)
        if DEBUGCPARSER>0:
            print text
        # create a pycparser
        parser = c_parser.CParser()

        # handle the error
        if ERRORDUMP:
            f = open('./__ipmacc_c_code_unable_to_parse.c','w')
            old_stdout = sys.stdout
            sys.stdout = f
            print text
            sys.stdout = old_stdout
            f.close()
            sys.stdout = old_stdout
        ast = parser.parse(text, filename='<none>')
        if ERRORDUMP:
            os.remove('__ipmacc_c_code_unable_to_parse.c')
        
        # generate the XML tree
#        ast.show()
#        codeAstXml = open('code_ast.xml','w')
#        ast.showXml(codeAstXml)
#        codeAstXml.close()
#        tree = ET.parse('code_ast.xml')
#        ast = parser.parse(text, filename='<none>')

        # generate the XML tree
        #ast.show()
        codeAstXml = open('code_ast.xml','w')
        ast.showXml(codeAstXml)
        codeAstXml.close()
        tree = ET.parse('code_ast.xml')
        os.remove('code_ast.xml')
        self.astRoot = tree.getroot()
#        root = tree.getroot()
#        return root.find(".//FuncDef/Compound")

#    def astCalcRoot(self):
#        text = self.var_parseForYacc(self.code)
#        if DEBUG>3:
#            print text
#        # create a pycparser
#        parser = c_parser.CParser()
#        ast = parser.parse(text, filename='<none>')
#
#        # generate the XML tree
#        #ast.show()
#        codeAstXml = open('code_ast.xml','w')
#        ast.showXml(codeAstXml)
#        codeAstXml.close()
#        tree = ET.parse('code_ast.xml')
#        os.remove('code_ast.xml')
#        self.astRoot = tree.getroot()



    def oacc_clauseparser_loop_isindependent(self,clause):
        # k=clause.replace('independent','independent()')
        #regex=re.compile(r'([A-Za-z0-9\ ]+)([\(])([A-Za-z0-9\ ]*)([\)])')
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        indep=False
        private=[]
        reduction=[]
        #for it in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            #print ''.join([i0,i1]).strip()
            #if ''.join([i0,i3]).strip()=='independent()':
            # dependent
            if i0.strip()=='independent':
                indep=True
            elif i0.strip()=='seq':
                indep=False
            # private vars
            elif i0.strip()=='private' and i3.strip()!='':
                #private=(i3.strip().replace(',',' ')+' '+private).strip()
                private.append(i3.strip())
            # reduction vars
            elif i0.strip()=='reduction' and i3.strip()!='':
                reduction.append(i3.strip())
            # reduction vars
        return [indep, private, reduction]

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

    def perform_implicit_copy(self,kernelId,scopeVarsNames,scopeVarsTypes,implicitCopies):
        code_copyin=''
        code_copyout=''
        if DEBUGCP>1:
            print 'Impilict Copy Checking for implicit copy'
        for var in implicitCopies:
            idx=scopeVarsNames.index(var)
            if DEBUGCP>1:
                print '\tretriving information of variable `'+var+'` ('+scopeVarsTypes[idx]+') for implicit copy'
    def oacc_privred_getVarNames(self, kernelId, listOfPrivorRed):
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        endList=[]
        corr=0
        for [kid, vlist] in listOfPrivorRed:
        #for [kid, vlist] in self.oacc_loopReductions:
            # each pair corresponds to a call which will be replaced with proper privatization or reduction
            if kid==kernelId:
                for vop in vlist.split(','):
                    vop=vop.replace(' ','').strip()
                    # find the varname, initvalue,
                    if vop.find(':')==-1:
                        # only privatization
                        #endList.append([vop,'0','U', corr])
                        operation='U'
                        variable=vop
                        initValu='0'
                    else:
                        # privatization and reduction
                        operation=vop.split(':')[0]
                        variable=vop.split(':')[1]
                        initValu='0'
                        if   operation=='+':
                            initValu='0'
                        elif operation=='*':
                            initValu='1'
                        elif operation=='min':
                            initValu='0'
                        elif operation=='max':
                            initValu='0'
                        elif operation=='&':
                            initValu='~0'
                        elif operation=='|':
                            initValu='0'
                        elif operation=='^':
                            initValu='0'
                        elif operation=='&&':
                            initValu='1'
                        elif operation=='||':
                            initValu='0'
                        else:
                            print 'Fatal Error! unexpected reduction operation ('+operation+') on variable '+variable
                            exit(-1)
                    # find the type
                    try :
                        idx=scopeVarsNames.index(variable)
                        type=scopeVarsTypes[idx]
                    except:
                        print 'Error: Could not determine the type of variable declared as private/reduction: '+variable
                        exit(-1)
                    endList.append([variable, initValu, operation, corr, type])
            corr+=1
        return endList

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
        if VERBOSE==1 and len(allFc)>0:
            print 'kernels region > Function calls: '+','.join(allFc)
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
        if VERBOSE==1 and len(vars)>0:
            print 'kernels region > Variables: '+', '.join(vars)
        # third, removed defined variables
        vars.remove(self.prefix_kernel_uid);
        for var in root.findall(".//Decl"):
            try :
                # ignore declared vars
                if DEBUGVAR:
                    print 'variable is defined: '+str(var.get('uid')).strip()
                vars.remove(str(var.get('uid')).strip())
            except :
                # it was a function call, ignore it
                k=True
        if VERBOSE==1 and len(vars)>0:
            print 'kernels region > The variables which aren\'t declared in the region: '+', '.join(vars)
        # fourth, listing all reduction variables of this kernel to:
        # 1) exclude from other copies
        # 2) allocate and transfer final value back to host
        privInfo=self.oacc_privred_getVarNames(kernelId,self.oacc_loopPrivatizin)
        reduInfo=self.oacc_privred_getVarNames(kernelId,self.oacc_loopReductions)
        # fourth, find the function arguments and implicit copies
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        kernelLoopIteratorsPar=self.oacc_kernelsLoopIteratorsPar[kernelId]
        kernelLoopIteratorsSeq=self.oacc_kernelsLoopIteratorsSeq[kernelId]
#        print 'again, kernel iterators > '+','.join(kernelLoopIteratorsPar)
        function_args=[]
        implicitCopies=[]
        for i in range(0,len(vars)):
            # 1- ignore iterator variables (we generate the code later)
#            print 'checking variable > \''+vars[i]+'\''
            itr=True
            try:
                idx=kernelLoopIteratorsPar.index(vars[i].strip())
            except:
                itr=False
            if itr:
                continue
            # 2- check if it is defined as automatic var
            autovar=False
            if len(self.oacc_kernelsAutomaPtrs)>0:
                for av in self.oacc_kernelsAutomaPtrs[kernelId].split(','):
                    if av.strip()==vars[i].strip():
                        autovar=True
                        break
            # 3- check if it is defined as manual var
            manualvar=False
            if len(self.oacc_kernelsManualPtrs):
                for mv in self.oacc_kernelsManualPtrs[kernelId].split(','):
                    if mv.strip()==vars[i].strip():
                        manualvar=True
                        break
            # 4- private/reduction variables (exclude from functionArgs for now)
            priv=False # if true, exclude the variable from functionArgs
            redu=False # if true, include a pointer to this variable
            for [priredV, priredI, priredO, corr, typ] in (privInfo+reduInfo):
                if priredV.strip()==vars[i].strip():
                    if priredO=='U':
                        priv=True
                    else:
                        redu=True
            if priv and redu:
                print 'warning: the variable is defined both as reduction and private, we assume the reduction (covering private too)'
                priv=False
            # 5- iterators of sequential loops undefined in the region (ignore declaration, we append latter)
            itr=True
            try:
                idx=kernelLoopIteratorsSeq.index(vars[i].strip())
            except:
                itr=False
            if itr:
                continue
            # 6- append function arguments, and find undefined variables (ignore non-pointer)
            undef=False
            pointr=False
            if not priv:
                try :
                    idx=scopeVarsNames.index(vars[i])
                    if scopeVarsTypes[idx].count('*')!=0:
                        # 7- is pointer
                        pointr=True
                    scalar_copy=(scopeVarsTypes[idx].count('*')==0) and manualvar
                    arg_type=scopeVarsTypes[idx]
                    arg_type+='* ' if (redu or scalar_copy) else ' '
                    arg_name=scopeVarsNames[idx]
                    arg_name+=('__ipmacc_scalar' if scalar_copy else '')
                    function_args.append(arg_type+arg_name)
                    #function_args.append(scopeVarsTypes[idx]+('* ' if redu else ' '))
                    #function_args.append(scopeVarsTypes[idx]+('* ' if (redu or not pointr)else ' ')+(scopeVarsNames[idx]+('__ipmacc_scalar' if ((not pointr) and (not redu)) else '')))
                except:
                    print 'WARNING: Could not determine the type of variable used in the kernel: '+vars[i]
                    print '\tignoring undefined variable, maybe a macro solves proble!'
                    undef=True
                    #exit (-1)
            # 8- track implicit copies
            if manualvar and autovar:
                print 'Warning: Confusion on declaration of variable `'+vars[i]+'`'
            elif not(undef or manualvar or autovar or (not pointr)):
                # the variable is implicitly defined on device
                # handle the copy-in/copyout
                implicitCopies.append(vars[i].strip())
        # five, perform implicit copies
        self.perform_implicit_copy(kernelId,scopeVarsNames,scopeVarsTypes,implicitCopies)
        # six, construct declaration of loop iterators (both parallel and sequential)
        code=''
#        for i in kernelLoopIteratorsPar:
#            code+='int '+i+';\n'
        for i in kernelLoopIteratorsPar+kernelLoopIteratorsSeq:
            try :
                idx=scopeVarsNames.index(i)
                code+=scopeVarsTypes[idx]+' '+i+';\n'
            except:
                print 'Error: Could not determine the type of loop iterator used in the kernel: '+i
                print '\tignoring undefined variable, maybe a macro solves proble!'

        # report stats
        if VERBOSE==1:
            if len(function_args)>0: print 'kernels region > kernel arguments: '+', '.join(function_args)
            if len(self.oacc_kernelsAutomaPtrs)>0: print 'kernels region > automatic vars (deviceptr)                 > '+self.oacc_kernelsAutomaPtrs[kernelId]
            if len(self.oacc_kernelsManualPtrs)>0: print 'kernels region > manual    vars (copy in, copy out, create) > '+self.oacc_kernelsManualPtrs[kernelId]
            print 'kernels region > implicit copy peformed for                 > '+','.join(implicitCopies)
        # return function args and early declaration part
        return [function_args, code, implicitCopies, privInfo, reduInfo]

    def kernel_forSize_CReadable(self, list):
        if len(list)==1 and not (type(list[0]) is str):
            return self.kernel_forSize_CReadable(list[0])
        max=[]
        prod=[]
        for ch in list:
            if type(ch) is str:
                prod.append(ch)
            else:
                j=self.kernel_forSize_CReadable(ch)
                if j!='':
                    max.append(j)
        if len(prod)>0 and len(max)>0:
            return '*'.join(prod)+'*'+'IPMACC_MAX'+str(len(max))+'('+','.join(max)+')'
        elif len(prod)>0:
            return '('+'*'.join(prod)+')'
        elif len(max)>0:
            return 'IPMACC_MAX'+str(len(max))+'('+','.join(max)+')'
        else:
            return ''

    def find_kernel_forSize_Recursive(self, root):
        # determining the total reguired threads for parallelism of every loop
        # and marking the lastlevel loop (leaves)
        accumulation=[]
        horizon=[]
        for ch in root:
            t=self.find_kernel_forSize_Recursive(ch)
            if len(t)>0:
                horizon.append(t)
        if len(horizon)>0:
            accumulation.append(horizon)
        if root.tag=='for' and root.attrib['independent']=='true':
            #accumulation.append(self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep')))
            if len(accumulation)==0:
                root.attrib['lastlevel']='true'
                accumulation.append(root.attrib.get('terminate'))
                root.attrib['dimloops']=self.kernel_forSize_CReadable(accumulation)
            else:
                root.attrib['lastlevel']='false'
                root.attrib['dimloops']=self.kernel_forSize_CReadable(accumulation)
                accumulation.append(root.attrib.get('terminate'))
            return accumulation
        else:
            return horizon

    def find_kernel_forSize(self, root):
        iterator_p=[]
        iterator_s=[]
        size=''
        forSize=[]
        for ch in root:
            [it_p, t, it_s]=self.find_kernel_forSize(ch)
            if t!='':
                forSize.append(t)
            if len(it_p)>0:
                iterator_p=iterator_p+it_p
            if len(it_s)>0:
                iterator_s=iterator_s+it_s
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
        if root.tag=='for' and root.attrib['independent']!='true' and len(root.attrib['initial'].split('=')[0].strip().split(' '))<2:
            # this iterator is undefined, yet non parallel
            iterator_s=iterator_s+[root.attrib.get('iterator')]
        if root.tag=='for' and root.attrib['independent']=='true':
            # append the for size
            iterator_p=iterator_p+[root.attrib.get('iterator')]
            return [iterator_p, '@'+self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'))+size, iterator_s]
        return [iterator_p, size, iterator_s]

    def carry_loopAttr2For(self, root, independent, private, reduction):
        # get kernels region and go through to carry loop clauses to the corresponding for
        # mark independent loops, private vars, reduction vars
        if root.tag=='pragma':
            if root.attrib.get('directive')=='kernels':
                for ch in root:
                    self.carry_loopAttr2For( ch, False, private, reduction)
            elif root.attrib.get('directive')=='loop':
                [indep,priv,reduc]=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                for ch in root:
                    self.carry_loopAttr2For(ch, indep, private+priv, reduction+reduc)
            else:
                print('Invalid: '+root.attrib.get('directive')+' directive in region!')
                exit(-1)
        elif root.tag=='for':
            # independent
            if independent:
                root.attrib['independent']='true'
            else :
                root.attrib['independent']='false'
            # cut private
            root.attrib['private']=','.join(private)
            # cut reduction
            root.attrib['reduction']=','.join(reduction)
            # go through the childs
            for ch in root:
                self.carry_loopAttr2For(ch, False, [], [])

    def var_kernel_genPlainCode(self, id, root, nesting):
        code=''
        try:
            if root.tag=='pragma':
                if root.attrib.get('directive')=='kernels':
                    code=code+'{\n'
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting)
                    code=code+'}\n'
                elif root.attrib.get('directive')=='loop':
                    [indep,priv,reduc]=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                    for ch in root:
                        #print str(indep)
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting)
                else:
                    print('Invalid: '+root.attrib.get('directive')+' directive in region!')
                    exit(-1)
            elif root.tag=='for':
                if root.attrib['independent']=='true': #independent:
                    if DEBUGLD:
                        print 'for loop of -> '+root.attrib['iterator']+' -> '+root.attrib['dimloops']
                    # generate indexing
                    if root.attrib['lastlevel']=='true':
                        # last-level
                        if nesting==0:
                            # single parallel loop
                            iteratorVal=(root.attrib.get('init')+root.attrib.get('incoperator'))+'('+self.prefix_kernel_uid+');'
                        else:
                            iteratorVal=(root.attrib.get('init')+root.attrib.get('incoperator'))+'('+self.prefix_kernel_uid+'%('+root.attrib['dimloops']+')'+');'
                    else:
                        # upper levels
                        iteratorVal=(root.attrib.get('init')+root.attrib.get('incoperator'))+'('+self.prefix_kernel_uid+'/('+root.attrib['dimloops']+')'+');'
                    code=code+root.attrib.get('iterator')+'='+iteratorVal+'\n'
                    # generate if statement
                    code=code+'if('+root.attrib.get('boundary')+')\n'
                    if root.attrib.get('private')!='' or root.attrib.get('reduction')!='':
                        # generate private/reduction declaration
                        separator=(',' if (root.attrib.get('private')!='' and root.attrib.get('reduction')!='') else '')
                        variables=root.attrib.get('private')+separator+root.attrib.get('reduction')
                        code+='{\n'
                        code=code+'/*private:'+variables+'*/\n'
                        code=code+self.prefix_kernel_privred_region+str(len(self.oacc_loopPrivatizin))+'();'+'\n'
                        self.oacc_loopPrivatizin.append([id,variables])
                    # go through childs
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting+1)
                    if root.attrib.get('reduction')!='':
                        # generate reduction operations
                        variables=root.attrib.get('reduction')
                        code=code+'/*reduction:'+variables+'*/\n'
                        code=code+self.prefix_kernel_reduction_region+str(len(self.oacc_loopReductions))+'();'+'\n'
                        self.oacc_loopReductions.append([id,variables])
                        code+='}\n'
                    # terminate if statement
                    code=code+'\n'
                else :
                    # generate `for` statement
                    code=code+self.code_gen_reversiFor(root.attrib.get('initial'),root.attrib.get('boundary'),root.attrib.get('increment'))+'\n'
                    # go through childs
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting)
                    # terminate for statement
                    #code=code+root.tag+'\n'
            elif root.tag=='c':
                code=code+root.text.strip()+'\n'
        except Exception as e:
            print 'exception! dumping the code:\n'+self.code+code
            print e
            exit(-1)
        return code

    def debug_dump_privredInfo(self, type, privredList):
        for [v, i, o, a, t] in privredList:
            print type+'> variable: '+v+' initialized: '+i+' operator: '+o+' assignee: '+str(a)+' type: '+t
    def generate_code(self):
        Argus=[]
        KBody=[]
        Decls=[]
        FDims=[]
        Privs=[]
        Redus=[]
        for i in range(0,len(self.oacc_kernels)):
            if DEBUGLD:
                print 'finding the kernel dimension (`for` size)...'
            [iterators_p, purestring, iterators_s]=self.find_kernel_forSize(self.oacc_kernels[i])
            #print 'it could be something like -> '+str(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
#            print 'it could be something like -> '+self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
            if DEBUGLD or DEBUGVAR:
                 print 'iterators  of parallel   loops :'+','.join(iterators_p)
                 print 'undeclared iterators  of sequential loops :'+','.join(iterators_s)
            iterators_p = list(set(iterators_p))
            self.oacc_kernelsLoopIteratorsPar.append(iterators_p)
            self.oacc_kernelsLoopIteratorsSeq.append(iterators_s)
            forDims=self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
            if DEBUGLD:
                print 'total concurrent threads -> '+forDims
            kernelBody=self.var_kernel_genPlainCode(i, self.oacc_kernels[i], 0)
            [args, declaration, implicitCopies, privInfo, reduInfo]=self.find_kernel_undeclaredVars_and_args(kernelBody, i)
            self.oacc_kernelsImplicit.append(implicitCopies)
            self.oacc_kernelsReductions.append(list(reduInfo))
            self.oacc_kernelsPrivatizin.append(list(privInfo))
            if DEBUGPRIVRED:
                self.debug_dump_privredInfo('private',privInfo)
                self.debug_dump_privredInfo('reduction',reduInfo)
            # carry the loop break
            Argus.append(args)
            KBody.append(kernelBody)
            Decls.append(declaration)
            FDims.append(forDims)
            Privs.append(privInfo)
            Redus.append(reduInfo)
        
        k.var_copy_assignExpDetail()
        k.var_copy_genCode()
        ##k.var_copy_showAll()
        ##k.varmapper_showAll()


        for i in range(0,len(self.oacc_kernels)):
            # carry the loop break
            args=        Argus[i]
            kernelBody=  KBody[i]
            declaration= Decls[i]
            forDims=     FDims[i]
            privInfo=    Privs[i]
            reduInfo=    Redus[i]
            if DEBUGPRIVRED:
                self.debug_dump_privredInfo('private',privInfo)
                self.debug_dump_privredInfo('reduction',reduInfo)
            # loop continue
            [kernelPrototype, kernelDecl]=self.codegen_constructKernel(args, declaration, kernelBody, i, privInfo, reduInfo, (self.blockDim_cuda if self.target_platform=='CUDA' else self.blockDim_opencl), forDims)
            self.codegen_appendKernelToCode(kernelPrototype, kernelDecl, i, forDims, args)


# check for codegen options
parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to output CU file", metavar="FILE", default="")
parser.add_option("-t", "--targetarch", dest="target_platform",
                  help="Target code (nvcuda or nvopencl)", default="")
(options, args) = parser.parse_args()

if options.target_platform=="":
    parser.print_help()
    exit(-1)
else:
    print 'The target code is '+options.target_platform

if options.filename=="":
    parser.print_help()
    exit(-1)
else:
    print 'The output file is : '+options.filename




# read the input XML which is validated by parser
tree = ET.parse('__inter.xml')
root = tree.getroot()
if CLEARXML:
    os.remove('__inter.xml')

# create a code generator module
k = codegen(options.target_platform)

# prepare the destination code by parsing the XML tree
k.code_descendentRetrieve(root,0)

if k.acc_detected():
    if not CLEARXML:
        k.code_kernelDump(0);
    k.codegen_includeHeaders()

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
    if DEBUGSTMBRK:
        print k.code
        for [typ,stm] in k.code_getAssignments(k.code,['def','inc','typ','str']):
            print typ+' : '+stm[0:40].replace('\n',' ').strip()+'...'
    k.generate_code()
else:
    print 'warning: no OpenACC region is detected.'


# prepare to write the code to output
k.code_descendentDump(options.filename)

print "code geneneration completed!"

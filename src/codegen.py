# version info: 1.1.0b

import sys
import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
#from termcolor import colored
import os
from random import randint

ipmaccprefix=os.path.dirname(os.path.realpath(__file__))+"/../"
sys.path.extend(['.', '..', ipmaccprefix+'/build/py/', ipmaccprefix+"/src/srcML-wrapper/"])
from pycparser import c_parser, c_ast
from utils_clause import clauseDecomposer,clauseDecomposer_break
from wrapper import srcml_code2xml, srcml_get_fcn_calls, srcml_get_var_details, srcml_get_parent_fcn, srcml_get_all_ids, srcml_get_declared_vars, srcml_find_var_size, srcml_get_fwdecls, srcml_prefix_functions,srcml_get_dependentVars,srcml_get_active_types,srcml_get_arrayaccesses,srcml_is_written

from subprocess import call, Popen, PIPE
import tempfile

from optparse import OptionParser
from collections import defaultdict
from inspect import currentframe, getframeinfo

# Operation control
ENABLE_INDENT=False
CLEARXML=True
VERBOSE=0
ERRORDUMP=True
REDUCTION_TWOLEVELTREE=True # two-level tree reduction is the default policy.
    # setting the control to False, generates only CUDA code which is supported on limited number of devices (cc>=1.3). 
USEPYCPARSER=False # True: pycparser (depreciated!), False: srcML
USEAPI=True # use API instead of hard-code for performing OpenCL kernel compilation
TAGBASEDSMC=False
WARNING=False
WARNINGSMC=False # warning in cache of smc pragma
PROFILER=False

# Debugging level control
DEBUG=0 #general
DEBUGCP=0 #copy statement
DEBUGREGEX=False
DEBUGCPARSER=0 #parsers
DEBUGVAR=False #variable type/size/name tracking
DEBUGLD=False   # loop detector
DEBUGPRIVRED=False #private/reduction statements
DEBUGSTMBRK=False
DEBUGFC=False #function call
DEBUGSRCML=False   #debugging srcml 
DEBUGSRCMLC=False #debugging srcml wrapper calls
DEBUGFWDCL=False  #debug forward declaration and function redeclaration
DEBUGITER=False 
DEBUGCPP=False #debug cpp call
DEBUGSMC=False
DEBUGMULTIDIMTB=False #True
DEBUGCACHE=False
DEBUGSMCPRECALCINDEX=False
DEBUGATOMIC=False
GENDEBUGCODE=False
#GENMULTIDIMTB=True
GENMULTIDIMTB=False #True
DEBUGSTL=False #debug std stl support
DEBUGENTEREXIT=False 
DEBUGSCALRVAR=False
DEBUGDETAILPROC=False #debug procedures providing detailed analysis of procedure calls
DEBUGCOMPRESSION=False # debug compression directive
DEBUGPRFR=False

# CACHE IMPLEMENTATION CONFIGURATION
CACHE_IMPL_MATHOD_RBI = 0
CACHE_IMPL_MATHOD_RBC = 1
CACHE_IMPL_MATHOD_EHC = 2 # not implemented
CACHE_IMPL_MATHOD = CACHE_IMPL_MATHOD_RBI
CACHE_RBX_POINTER_TYPE_COMMUN  = 0
CACHE_RBX_POINTER_TYPE_PRIVATE = 1
CACHE_RBX_POINTER_TYPE = CACHE_RBX_POINTER_TYPE_COMMUN
CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_SYNC  = 0
CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_ARG   = 1
CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_FIXED = 2
CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD = CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_FIXED

def print_error(err_msg, details):
    print 'internal error:', err_msg
    for s in details:
        print s
    print 'aborting()'
    exit(-1)

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
class compVar(object):
    def __init__(self, varName):
        self.varName=varName
        self.type=""
        self.min=""
        self.max=""
        self.scope=""
        self.compLevel=""
class codegen(object):


    def __init__(self, target, foname, nvcc_args, optimizations, perforationconf):
        self.oacc_kernelId=0     # number of kernels which are replaced by function calls
        self.oacc_kernels=[]     # array of kernels' roots (each element of array is ElementTree)
        self.oacc_kernelsParent=[]   # array of functions name, indicating which function is the parent of kernel (associated with each elemnt in self.oacc_kernels)
        self.oacc_kernelsVarNams=[] # list of array of variables defined in the kernels' call scope
        self.oacc_kernelsVarTyps=[] # list of array of type of variables defined in the kernels' call scope
        self.oacc_kernelsLocalVarNams=[] # same as oacc_kernelsVarNams, but only declared within the kernel locally
        self.oacc_kernelsLocalVarTyps=[] # same as oacc_kernelsVarTyps, but only declared within the kernel locally
        self.oacc_kernelsLoopIteratorsPar=[]   # list of array of iterators of independent/parallel loops
        self.oacc_kernelsLoopIteratorsSeq=[]   # list of array of iterators of sequential loop
        self.oacc_kernelsAutomaPtrs=[]  # per kernel list of variables defined as deviceptr in the respective kernels or data region (no action)
        self.oacc_kernelsManualPtrs=[]  # per kernel list of variables defined explicitly to be copied in, copied out, or allocated in the respective kernels or data region 
        self.oacc_kernelsImplicit=[] # implicit copies corresponding to this kernel
        self.oacc_kernelsReductions=[] # per kernel list of variable to be reduced (used for copy-in copy-out)
        self.oacc_kernelsPrivatizin=[] # per kernel list of variable to be privated (used for copy-in copy-out)
        self.oacc_kernelsTemplates=[] # templates corresponding to each kernel
        self.oacc_kernelsAssociatedCopyIds=[] # a list of oacc_copys identifiers associated with each kernel
        self.oacc_kernelsComp=[] # per kernel list of compression() variables declared over kernels directive
        self.oacc_loopSMC=[] # per call list of variables to be cached in SMC
        self.oacc_loopReductions=[] # per call list of variable to be reduced 
        self.oacc_loopPrivatizin=[] # per call list of variable to be privated 
        self.oacc_scopeAutomaPtr='' # carry the variables which are deviceptrs across the current data (not kernels) region scope
        self.oacc_scopeManualPtr='' # carry the variables which are declared explicitly for copy or allocate in current data (not kernels) region scope

        self.oacc_copyId=0  # number of copys which are replaced by function calls
        self.oacc_copys=[]  # array of copys' expression (each element is string)
        self.oacc_copysParent=[]   # array of functions name, indicating the function which is the parent of copy (associated with each elemnt in self.oacc_copys)
        self.oacc_copysVarNams=[] # list of array of variables defined in the copys' call scope
        self.oacc_copysVarTyps=[] # list of array of type of variables defined in the copys' call scope
        self.oacc_constCoefDefs='' # codes of constant memory definitions for stroring compression coefficients
        self.oacc_kernelsConfig=[] # per kernel configuration, namely blockDimx, blockDimy, blockDimz,
        self.oacc_atomicReg=[] # per call list of atomic regions
        self.oacc_algoReg=[] # per call list of algorithm directives
        self.oacc_algoSort_Types2Overload = [] # list of data types to overload compare function of sorts for
        self.oacc_algoFind_Types2Overload = [] # list of data types to overload compare function of finds for
        self.oacc_extra_symbols=[] # per kernel list of symbol names which should be known in the kernels region, but are skipped for some reasons
        
        self.code='' # intermediate generated C code
        self.code_include='#include <stdlib.h>\n#include <stdio.h>\n#include <assert.h>\n#include <openacc.h>\n' # .h code including variable decleration and function prototypes
        #self.code_include='#include <stdlib.h>\n#include <stdio.h>\n#include <assert.h>\n#include <openacc.h>\nvoid ipmacc_prompt(char *s){\nif (getenv("IPMACC_VERBOSE"))\nprintf("%s",s);\n}\n' # .h code including variable decleration and function prototypes
        self.code_include+='#define IPMACC_MAX1(A)   (A)\n'
        self.code_include+='#define IPMACC_MAX2(A,B) (A>B?A:B)\n'
        self.code_include+='#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))\n'
        self.code_include+='#ifdef __cplusplus\n#include "openacc_container.h"\n#endif\n\n'
        self.active_types=[] # list of types which have at least one variable in the region scope
                             # keep track of types used in this code to forward declare undeclared types
        self.active_types_decl=[] # list of tuple (type name, type forward declaration, and full declaration, second forward declaration, recursion type parent)
                             # declaration of active types which are not standard
        self.active_calls=[] # list of types which have at least one variable in the region scope
                             # keep track of calls used in this code to declare them
        self.active_calls_decl=[] # list of tuple (call name, and call forward declaration)
                             # declaration of active calls which are not standard
        self.func_comp_vars=defaultdict(list) # list of tuples:[local compressed variable,kernel compressed variable] for each active_calls_decl (func_comp_vars[funcName]=[function local compressed variable, kernel compressed variable]) 
        self.intrinsic_calls_ocl= [ 'acos', 'acosh', 'acospi', 'asin', 'asinh', 'asinpi', 'atan', 'atan2', 'atanh', 'atanpi', 'atan2pi',
                                'cbrt', 'ceil', 'copysign', 'cos', 'cosh', 'cospi', 'erfc', 'erf', 'exp', 'exp2', 'exp10', 'expm1',
                                'fabs', 'fdim', 'floor', 'fma', 'fmax', 'fmin', 'fmod', 'fract', 'frexp', 'hypot', 'ilogb', 'ldexp',
                                'lgamma', 'lgamma_r', 'log', 'log2', 'log10', 'log1p', 'logb', 'mad', 'maxmag', 'minmag', 'modf',
                                'nan', 'nextafter', 'pow', 'pown', 'powr', 'remainder', 'remquo', 'rint', 'rootn', 'round', 'rsqrt',
                                'sin', 'sincos', 'sinh', 'sinpi', 'sqrt', 'tan', 'tanh', 'tanpi', 'tgamma', 'trunc', 'half_cos',
                                'half_divide', 'half_exp', 'half_exp2', 'half_exp10', 'half_log', 'half_log2', 'half_log10', 'half_powr',
                                'half_recip', 'half_rsqrt', 'half_sin', 'half_tan', 'native_cos', 'native_divide', 'native_exp', 'native_exp',
                                'native_exp2', 'native_exp10', 'native_log', 'native_log2', 'native_log10', 'native_powr', 'native_recip',
                                'native_rsqrt', 'native_sin', 'native_sqrt',
                                'abs', 'abs_diff', 'add_sat', 'hadd', 'rhadd', 'clamp', 'clz', 'mad_hi', 'mad_sat', 'max', 'min', 
                                'mul_hi', 'rotate', 'sub_sat', 'upsample', 'mad24', 'mul24',
                                'clamp', 'degrees', 'max', 'min', 'radians', 'step', 'smoothstep', 'sign', 'cross', 'dot', 'distance', 'length', 
                                'normalize', 'fast_distance', 'fast_normalize', 'isequal', 'isnotequal', 'isgreater', 'isgreaterequal', 
                                'isless', 'islessequal', 'islessgreater', 'isfinite', 'isinf', 'isnan', 'isnormal', 'isordered', 'isunordered',
                                'signbit', 'any', 'all', 'bitselect', 
                                'vloadn', 'vstoren', 'vload_half', 'vload_halfn',
                                'vstore_half', 'vstore_half_rte', 'vstore_half_rtz', 'vstore_half_rtn', 'vstore_half_rtp', 
                                'vstore_halfn', 'vstore_halfn_rte', 'vstore_halfn_rtz', 'vstore_halfn_rtn', 'vstore_halfn_rtp', 
                                'prefetch' ]
                                # opencl calls which are available within kernel
        self.intrinsic_calls_cuda= [ 'rsqrtf', 'rsqrtf', 'sqrtf', 'cbrtf', 'rcbrtf', 'hypotf', 'expf', 'exp2f', 'exp10f', 'expm1f', 
                                'logf', 'log2f', 'log10f', 'log1pf', 'sinf', 'cosf', 'tanf', 'sincosf', 'sinpif', 'cospif', 
                                'asinf', 'acosf', 'atanf', 'atan2f', 'sinhf', 'coshf', 'tanhf', 'asinhf', 'acoshf', 'atanhf', 
                                'powf', 'erff', 'erfcf', 'erfinvf', 'erfcinvf', 'erfcxf', 'lgammaf', 'tgammaf', 'fmaf', 'frexpf', 
                                'ldexpf', 'scalbnf', 'scalblnf', 'logbf', 'ilogbf', 'j0f', 'j1f', 'jnf', 'y0f', 'y1f', 
                                'ynf', 'fmodf', 'remainderf', 'remquof', 'modff', 'fdimf', 'truncf', 'roundf', 'rintf', 'nearbyintf', 
                                'ceilf', 'floorf', 'lrintf', 'lroundf', 'llrintf', 'llroundf', 'sqrt', 'rsqrt', 'cbrt', 'rcbrt', 
                                'hypot', 'exp', 'exp2', 'exp10', 'expm1', 'log', 'log2', 'log10', 'log1p', 'sin', 
                                'cos', 'tan', 'sincos', 'sinpi', 'cospi', 'asin', 'acos', 'atan', 'atan2', 'sinh', 
                                'cosh', 'tanh', 'asinh', 'acosh', 'atanh', 'pow', 'erf', 'erfc', 'erfinv', 'erfcinv', 
                                'erfcx', 'lgamma', 'tgamma', 'fma', 'frexp', 'ldexp', 'scalbn', 'scalbln', 'logb', 'ilogb', 
                                'j0', 'j1', 'jn', 'y0', 'y1', 'yn', 'fmod', 'remainder', 'remquo', 'modf', 
                                'fdim', 'trunc', 'round', 'rint', 'nearbyint', 'ceil', 'floor', 'lrint', 'lround', 'llrint', 
                                'llround', 'x/y', 'sinf', 'cosf', 'tanf', 'sincosf', 'logf', 'log2f', 'log10f', 'expf', 
                                'exp10f', 'powf', '__fadd_', '__fmul_', '__fmaf_', '__frcp_', '__fsqrt_', '__fdiv_', '__fdividef', '__expf', 
                                '__exp10f', '__logf', '__log2f', '__log10f', '__sinf', '__cosf', '__sincosf', '__tanf', '__sinf', '__powf', 
                                'exp2f', '__dadd_', '__dmul_', '__fma_', '__ddiv_', '__drcp_', '__dsqrt_']
                                # cuda calls which are available in the kernel
        self.intrinsic_types_cuda= [ 'char1', 'uchar1', 'char2', 
                                'uchar2', 'char3', 'uchar3', 'char4', 'uchar4', 'short1', 'ushort1', 'short2', 'ushort2', 'uint2', 
                                'int3', 'uint3', 'int4', 'uint4', 'long1', 'ulong1', 'short3', 'ushort3', 'short4', 'ushort4', 
                                'int1', 'uint1', 'int2', 'long2', 'ulong2', 'long3', 'ulong3', 'long4', 'ulong4', 'longlong1', 
                                'ulonglong1', 'longlong2', 'ulonglong2', 'float1', 'float2', 'float3', 'float4',
                                'double1', 'double2', 'double3', 'double4']
                                # cuda types which are available
        self.intrinsic_types_ocl = [ 'char2', 'char3', 'char4', 'char8', 'char16',
        'uchar2', 'uchar3', 'uchar4', 'uchar8', 'uchar16',
        'short2', 'short3', 'short4', 'short8', 'short16',
        'ushort2', 'ushort3', 'ushort4', 'ushort8', 'ushort16',
        'int2', 'int3', 'int4', 'int8', 'int16',
        'uint2', 'uint3', 'uint4', 'uint8', 'uint16',
        'long2', 'long3', 'long4', 'long8', 'long16',
        'ulong2', 'ulong3', 'ulong4', 'ulong8', 'ulong16',
        'float2', 'float3', 'float4', 'float8', 'float16',
        'double2', 'double3', 'double4', 'double8', 'double16' ]

        self.code_kernels=[] # list of code generated for kernels
        self.nvcc_args=nvcc_args
        # configure codegenerator to enable optimizations 
        self.optimizations=optimizations
        self.optimizations_valid=['readonlycache'
                                  ]
        for opt1 in optimizations.split(','):
            found= opt1.strip() in self.optimizations_valid
            if not found and opt1.strip()!='':
                print 'invalid optimization switch: '+opt1
                exit(-1)
        self.opt_readonlycache= 'readonlycache' in optimizations.split(',')
        # configure codegenerator to enable perforations
        perforationfixtp = perforationconf.split(',')[0]
        perforationgrids = perforationconf.find('shrink')!=-1

        self.perforationshrink = perforationgrids
        self.perforationfixtyp = perforationfixtp if perforationfixtp!='' else 'non'
        self.perforationfixtyp_valid=['non',
                                      'fixcpy',
                                      'fixavg',
                                      'fixmin',
                                      'fixmax',
                                      'fixwav'
                                      ]
        self.perforationrates = [] # list of pair of perforation rate and kernel id
        if self.perforationfixtyp.strip()!='' and (not self.perforationfixtyp in self.perforationfixtyp_valid):
            print_error('invalid perforation type '+self.perforationfixtyp, [])

        # variable mapper
        self.varmapper=[]   # tuple of (function_name, host_variable_name, device_variable_name)
        self.varmapper_allocated=[]
        self.prefix_varmapper = '__autogen_device_'
        self.suffix_present = '_prstn'

        # constants
        self.prefix_kernel='__ungenerated_kernel_region_'
        self.prefix_kernel_gen='__generated_kernel_region_'
        self.prefix_kernel_lau='__generated_kernel_launch_'
        self.prefix_datacp='__ungenerated_data_copy_'
        self.prefix_datacpin='__ungenerated_data_copyin_'
        self.prefix_datacpout='__ungenerated_data_copyout_'
        self.prefix_dataalloc='__ungenerated_data_alloc_'
        self.prefix_dataimpli='__ungenerated_implicit_data'
        self.prefix_kernel_uid_x='__kernel_getuid_x'
        self.prefix_kernel_uid_y='__kernel_getuid_y'
        self.prefix_kernel_uid_z='__kernel_getuid_z'
        self.prefix_kernel_reduction_shmem='__kernel_reduction_shmem_'
        self.prefix_kernel_reduction_region='__kernel_reduction_region_'
        self.prefix_kernel_privred_region='__kernel_privred_region_'
        self.prefix_kernel_smc_fetch='__kernel_smc_fetch_' # it may encompass fetch/initilization for one or more arrays
        self.prefix_kernel_smc_fetchend='__kernel_smc_fetchend_' # it may encompass fetch/initilization for one or more arrays
        self.prefix_kernel_smc_startpointer='__kernel_smc_startpointer_' # it may encompass fetch/initilization for one or more arrays
        self.prefix_kernel_smc_endpointer='__kernel_smc_endpointer_' # it may encompass fetch/initilization for one or more arrays
        self.prefix_kernel_smc_varpref='__kernel_smc_var_data_' 
        self.prefix_kernel_smc_tagpref='__kernel_smc_var_tag_' 
        self.prefix_kernel_reduction_iterator='__kernel_reduction_iterator'
        self.prefix_kernel_reduction_lock='__ipmacc_reduction_lock_'
        self.prefix_kernel_reduction_array='__ipmacc_reduction_array_'
        self.prefix_kernel_atomicRegion='__ipmacc_atomicRegion_' 
        self.prefix_kernel_atomicLocks='__ipmacc_atomicLocks' 
        self.atomicRegion_nlocks=10
        self.atomicRegion_locktype='unsigned int '
        self.prefix_kernel_algoRegion='__ipmacc_algoRegion_' 
        self.algorithm_execution_width=[]
        self.cuda_shared_memory_dynamic_alloc=[]
        #self.blockDim='256'
        self.blockDim_cuda='256'
        self.blockDim_cuda_xyz='16'
        self.blockDim_opencl='256'

        # ast tree
        self.astRoot=0
        self.astRootML=0
    
        # codegeneration control
        self.target_platform = 'none'
        if   target=='nvcuda':
            self.target_platform='CUDA'
        elif target=='nvopencl':
            self.target_platform='OPENCL'
        elif target=='intelispc':
            self.target_platform='ISPC'
            #print 'ISPC is not implemented!'
            #exit(-1)
        else:
            print 'Error: unknown backend! '+target
            exit(-1)

        # cuda carriers
        self.cuda_kernelproto=''
        self.cuda_kerneldecl =''

        # ispc carriers
        self.ispc_kernelproto=''
        self.ispc_kerneldecl=''

        # output file
        self.foname = foname

    # Set of functions for supporting STD STL Container Classes (and beyond!)
    def container_class_get_libclstyp(self, type):
        try:
            tlib=type.split('::')[0].strip()
            tcls=type.split('::')[1].split()[0].strip()
            if type.count('<')>1:
                print 'Error: nested containers are not supported!'
                print '\tunsupported datatype: '+type
                exit(-1)
            ttyp=type.split('<')[1].split('>')[0].strip()
        except:
            tlib=''
            tcls=''
            ttyp=''
        return [tlib, tcls, ttyp]
    def container_class_supported(self, type):
        [tlib, tcls, ttyp]=self.container_class_get_libclstyp(type)
        if DEBUGSTL: print 'looking for '+tlib+' :: '+tcls+' class support'
        supported_types=[
            ('std','vector'),
            ('std','anothercontainer')
            ]
        for (lib,cls) in supported_types:
            if tlib==lib and tcls==cls:
                if DEBUGSTL: print 'STD STL container class support found for '+type
                return True
        return False
    def container_class_pseudo(self, type):
        [tlib, tcls, ttyp]=self.container_class_get_libclstyp(type)
        if tlib=='std' and tcls=='vector':
            straighftype=['int', 'float', 'double', 'short', 'unsigned',
                'short', 'char', 'long']
            for spt in straighftype:
                if spt==ttyp:
                    return spt+'*'
        print 'Error: unable to find proper pseudo type for '+type
        exit(-1)
    # auxilary functions
    # - replace 1 from the end of string
    def replace_last(self, source_string, replace_what, replace_with):
        head, sep, tail = source_string.rpartition(replace_what)
        return head + replace_with + tail

    def acc_detected(self):
        return len(self.oacc_kernels)>0
    
    def wrapFuncName(self, fname):
        return fname.replace(',','_')

    def print_loopAttr(self,root):
        str ='Loop attribute> '
        str+='independent="'+root.attrib.get('independent')+'" '
        str+='private="'+root.attrib.get('private')+'" '
        str+='reduction="'+root.attrib.get('reduction')+'" '
        str+='gang="'+root.attrib.get('gang')+'" '
        str+='vector="'+root.attrib.get('vector')+'" '
        str+='smc="'+root.attrib.get('smc')+'" '
        str+='terminate="'+root.attrib.get('terminate')+'" '
        str+='init="'+root.attrib.get('init')+'" '
        str+='incoperator="'+root.attrib.get('incoperator')+'" '
#        str+='dimloops="'+root.attrib.get('dimloops')+'" '
        print str

    def unique_priv_list(self, privred):
        unq_list=[]
        for [priredV, priredI, priredO, corr, typ, depth] in privred:
            unq=True
            for [UpriredV, UpriredI, UpriredO, Ucorr, Utyp, Udepth] in unq_list:
                if (priredV==UpriredV and priredI==UpriredI and priredO==UpriredO and corr==Ucorr and typ==Utyp and depth==Udepth):
                    unq=False
                    break
            if unq:
                unq_list.append([priredV, priredI, priredO, corr, typ, depth])
        return unq_list
        
    #
    #
    # forward declaration
    def clear_type(self, tp):
        return ' '.join(tp.replace('*','').strip().split())
    def iskeyword_or_predeftyp(self, id):
        keywords=[  'for', 'if', 'while',
                'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum', 'extern',
                'float', 'for', 'goto', 'if', 'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
                'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while',
                'inline', '_Bool', '_Complex', '_Imaginary',
                '__FUNCTION__', '__PRETTY_FUNCTION__', '__alignof', '__alignof__', '__asm',
                '__asm__', '__attribute', '__attribute__', '__builtin_offsetof', '__builtin_va_arg',
                '__complex', '__complex__', '__const __extension__', '__func__', '__imag', '__imag__',
                '__inline', '__inline__', '__label__', '__null', '__real', '__real__',
                '__restrict', '__restrict__', '__signed', '__signed__', '__thread', '__typeof',
                '__volatile', '__volatile__',
                'restric']
        try:
            idx=keywords.index(id)
        except:
            return False
        return True
    def get_builtin_types(self):
        #tp=self.clear_type(tp)
        # FIXME: it might be necessary to separate the list of built-in type for each backend 
        types =['signed char', 'unsigned char', 'char', 'short int', 'unsigned short int', 'int', 'unsigned int', 'long int', 'unsigned long int', 'long long int', 'unsigned long long int']
        types+=['float', 'double', 'long double', 'float _Complex']
        types+=['double _Complex', 'long double _Complex']
        types+=['__complex__ float', '__complex__ double', '__complex__ long double', '__complex__ int']
        types+=['long long unsigned int', 'bool']
        return types
    def is_builtin_type(self, tp):
        #tp=self.clear_type(tp)
        types = self.get_builtin_types()
        try:
            idx=types.index(tp)
        except:
            return False
        return True
    def forward_declare_append_new_types(self, listOfType):
        self.active_types+=listOfType
        self.active_types=list(set(self.active_types))

    def forward_declare_dumps_types(self):
        for i in self.active_types:
            print 'declared type: "'+i+'"'

    def implant_function_prototypes(self):
        if self.target_platform=='CUDA':
            self.code=srcml_prefix_functions(self.code, self.oacc_kernelsParent)
        elif self.target_platform=='OPENCL':
            nop=True
        elif self.target_platform=='ISPC':
            self.code=srcml_prefix_functions(self.code, self.oacc_kernelsParent)
        else:
            print 'error: unimplemented platform #'+str(getframeinfo(currentframe()).lineno)
    
    def append_additional_args(self, active_calls):
        #modified_active_calls=[]
        additional_params = {}
        for [call, proto, body, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in active_calls:
            [params_t, params_v, params_s] = params
            [local_t, local_v, local_s]  = local_vars
            [scope_t, scope_v, scope_s]  = scope_vars
            # find global variables
            additional_vars = []
            for v in ids:
                v=v.strip()
                iskeyword=self.iskeyword_or_predeftyp(v)
                istype=True
                isparam=True
                islocal=True
                iscall =True
                isfname=True if call==v else False
                try:
                    scope_t.index(v)
                except:                
                    istype=False
                try:
                    params_v.index(v)
                except:                
                    isparam=False
                try:
                    local_v.index(v)
                except:
                    islocal=False
                try:
                    fcalls.index(v)
                except:
                    iscall=False
                if not (iskeyword or istype or isparam or islocal or iscall or isfname):
                    if DEBUGDETAILPROC: print v+' is global'
                    # first check if it is redundant or not
                    redundant = False
                    for [tmp_v, tmp_t, tmp_s] in additional_vars:
                        if v==tmp_v:
                            redundant = True
                            #print 'merged '+tmp_v+' on '+call
                            if tmp_t!=scope_t[scope_v.index(v)].strip():
                                print 'warning: confused with naming: '+v+' is both defined as '+tmp_t+' and '+scope_t[scope_v.index(v)].strip()+' codegen.py: '+str(getframeinfo(currentframe()).lineno)
                            break
                    if not redundant:
                        print 'scope_t: ', str(scope_t)
                        print 'scope_s: ', str(scope_s)
                        print 'scope_v: ', str(scope_v)
                        print 'call: ', call
                        print 'proto: ', proto
                        print 'v: ', v
                        additional_vars.append([v, scope_t[scope_v.index(v)].strip(), scope_s[scope_v.index(v)].strip()])
                else:
                    if False and DEBUGDETAILPROC: print v+' is '+' '.join([str(iskeyword), str(isparam), str(islocal), str(iscall), str(isfname)])
            # FIXME: append compression args to additional_vars
            if len(additional_vars)>0:
                additional_params[call] = additional_vars
            #modified_active_calls.append([call, proto, body, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids])

        for key in additional_params:
            additional_vars = additional_params[key]
            if DEBUGDETAILPROC: print 'key> '+key
            if DEBUGDETAILPROC: print additional_vars
            for [call, proto, body, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in active_calls:
                if DEBUGDETAILPROC: print ' checking the call '+call+' fcalls> '+','.join(fcalls)
                # find if the `call' reaches key through nested calls.
                callstovisit=list(set(fcalls))
                callsvisited=[]
                reachable=False #inflate
                while True:
                    newcalls=[]
                    for c2v in callstovisit:
                        if c2v==key:
                            reachable=True
                            break
                        for [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11] in active_calls:
                            if p1==c2v:
                                #print 'found the call to '+p1
                                newcalls += [item for item in p9 if (item not in callsvisited) and (item not in callstovisit)]
                    #print 'newcalls> '+','.join(newcalls)
                    if len(newcalls)>0:
                        callsvisited+=callstovisit
                        callstovisit=newcalls
                    if len(newcalls)==0 or reachable:
                        break
                if reachable or call==key:
                    if DEBUGDETAILPROC: print 'appending vars to '+call+' arguments'
                    [ex_params_t, ex_params_v, ex_params_s] = ex_params
                    for [v, t, s] in additional_vars:
                        ex_params_t.append(t)
                        ex_params_v.append(v)
                        ex_params_s.append(s)
        #return modified_active_calls

    def forward_declare_find(self):
        # find the declaration of the undeclared calls/types listed in self.active_calls and self.active_types
        codein=self.preprocess_by_gnu_cpp(self.code)
        # the declaration will be stored in self.active_calls_decl and self.active_types_decl for future uses
        # 1) determine the list undeclared function calls
        undecls_calls=[]
        for i in self.active_calls:
            if i.find('__kernel_privred_region_')==-1 and i.find('__kernel_reduction_region_')==-1:
                undecls_calls.append(i)
        undecls_calls=list(set(undecls_calls))
        # 2) determine the list of undeclared types
        active_types_in_fcns = srcml_get_active_types(codein, undecls_calls, self.intrinsic_calls_cuda if self.target_platform=='CUDA' else self.intrinsic_calls_ocl)
        undecls_types=[]
        self.active_types = list(set(self.active_types+active_types_in_fcns))
        for i in self.active_types:
            tp=self.clear_type(i)
            if not self.is_builtin_type(tp):
                undecls_types.append(tp)
        undecls_types=list(set(undecls_types))
        # 3) debugging
        if DEBUGFWDCL:
            print 'looking for declaration of following types: "'+'" "'.join(undecls_types)+'"'
            print 'looking for declaration of following calls: "'+'" "'.join(undecls_calls)+'"'
        # 4) find the declaration
        [self.active_types_decl, self.active_calls_decl] = srcml_get_fwdecls(codein, undecls_types, undecls_calls, self.intrinsic_calls_cuda if self.target_platform=='CUDA' else self.intrinsic_calls_ocl, self.get_builtin_types(), self.target_platform)
        self.append_additional_args(self.active_calls_decl)
        # 5) debugging
        if DEBUGFWDCL or DEBUGDETAILPROC:
            decls=self.active_types_decl
            for i in range(0,len(decls)):
                [type, fw_decl, full_decl, ocl_full_decl, ocl_parent]=decls[i]
                print '===== forward declarations '+str(i)+': type<'+type+'> fwdecl<'+fw_decl+'> fulldecl<'+full_decl+'> oclfulldecl<'+ocl_full_decl+'> oclparent<'+ocl_parent+'>'
            decls=self.active_calls_decl
            for i in range(0,len(decls)):
                [call, proto, body, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params]=decls[i]
                [params_t, params_v, params_s] = params
                [local_t, local_v, local_s]  = local_vars
                [scope_t, scope_v, scope_s]  = scope_vars
                [ex_params_t, ex_params_v, ex_params_s] = ex_params
                print '===== forward declarations '+str(i)+': call<'+call+'> prototype<'+proto+'> fulldecl<'+body+'> params_t<'+','.join(params_t)+'> params_v<'+','.join(params_v)+'> ex_params_t<'+','.join(ex_params_t)+'> ex_params_v<'+','.join(ex_params_v)+'> qualifiers<'+','.join(qualifiers)+'>'
    #
    # various
    def is_function_of_iterator_var(self, kernelId, kernelB, statement):
        listOfIterators=self.oacc_kernelsLoopIteratorsPar[kernelId]
        operands=['+', '-', '*', '(', ')', '&', '^', '%', '/']
        vars=[statement]
        for op in operands:
            varsT=[]
            for v in vars:
                varsT+=v.split(op)
            vars=varsT
        [srcmlO1, srcmlO2, srcmlO3, srcmlO4] = srcml_get_dependentVars(srcml_code2xml(kernelB),vars)
        # print 'iterators:', ','.join(listOfIterators)
        # print 'statement:', statement
        # print 'vars:', vars
        # print srcmlO1
        # print srcmlO2
        # print srcmlO3
        # print srcmlO4
        # print 'kernel:', kernelB

        for v1 in listOfIterators:
            for v2 in vars:
                if v1.strip()==v2.strip():
                    if WARNINGSMC: print 'SMC warning: found pivot element dependent on loop iterators!\n\t'+v1+'\t'+v2
                    return True
            for vList in srcmlO3:
                for v2 in vList:
                    #print v1+' '+v2
                    if v1.strip()==v2.strip():
                        if WARNINGSMC: print 'SMC warning: found pivot element dependent on loop iterators!\n\t'+v1+'\t'+v2
                        return True
        return False

    def get_preferred_blockDim(self, kernelId):
        blockDimx=''
        blockDimy=''
        blockDimz=''
        for [algoKId, algoId, algoBody, algoClause, revdepnest] in self.oacc_algoReg:
            if algoKId==kernelId:
                # reconfig this kernel
                if revdepnest=='0':
                    blockDimx=self.algo_get_preferred_width(kernelId) #self.algorithm_execution_width
                    blockDimy='2'
                    blockDimz='2'
                else:
                    print 'error: algorithm only supported in the most inner loop!'
                    print 'aborting()'
                    exit(-1)
        return [blockDimx, blockDimy, blockDimz]
    #
    # kernel configuration
    def oacc_kernelsConfig_getDecl(self, kernelId):
        try:
            row=self.oacc_kernelsConfig[kernelId]
        except:
            print 'index out of range! '+str(kernelId)+' '+str(len(self.oacc_kernelsConfig))
            exit(-1)
        ndim=0
        try:
            blockDimx=row['blockDimx'][0]
            ndim+=1
        except:
            blockDimx=''
        try:
            blockDimy=row['blockDimy'][0]
            ndim+=1
        except:
            blockDimy=''
        try:
            blockDimz=row['blockDimz'][0]
            ndim+=1
        except:
            blockDimz=''
        
        # get preferred block sizes from static code analysis
        [blockDimx_reconf, blockDimy_reconf, blockDimz_reconf] = self.get_preferred_blockDim(kernelId)

        # normalize
        if   ndim==3:
            if blockDimx=='PREDEF':
                blockDimx=blockDimx_reconf if blockDimx_reconf!='' else self.blockDim_cuda_xyz
            if blockDimy=='PREDEF':
                blockDimy=blockDimy_reconf if blockDimy_reconf!='' else self.blockDim_cuda_xyz
            if blockDimz=='PREDEF':
                blockDimz=blockDimz_reconf if blockDimz_reconf!='' else '4' #self.blockDim_cuda_xyz
        elif ndim==2:
            if blockDimx=='PREDEF':
                blockDimx=blockDimx_reconf if blockDimx_reconf!='' else self.blockDim_cuda_xyz
            if blockDimy=='PREDEF':
                blockDimy=blockDimy_reconf if blockDimy_reconf!='' else self.blockDim_cuda_xyz
        elif ndim==1:
            if blockDimx=='PREDEF':
                blockDimx=blockDimx_reconf if blockDimx_reconf!='' else self.blockDim_cuda
        return [ndim, blockDimx, '1' if blockDimy=='' else blockDimy, '1' if blockDimz=='' else blockDimz]
    def oacc_kernelsConfig_update(self, kernelId, loopDim, nesting):
        #print 'called> '+str(kernelId)+' '+loopDim
        if len(self.oacc_kernelsConfig)<=kernelId:
            row={'blockDimx':[loopDim,nesting]}
            self.oacc_kernelsConfig.append(row)
        else:
            # extract dims from row 
            ndim=0
            row=self.oacc_kernelsConfig[kernelId]
            try:
                blockDimx=row['blockDimx']
                ndim+=1
            except:
                blockDimx=''
            try:
                blockDimy=row['blockDimy']
                ndim+=1
            except:
                blockDimy=''
            try:
                blockDimz=row['blockDimz']
                ndim+=1
            except:
                blockDimz=''
            # 
            if ndim==3:
                if blockDimx[1]==nesting:
                    # parallelism at the same nesting
                    row={'blockDimx':[loopDim, nesting], 'blockDimy':blockDimy, 'blockDimz':blockDimz}
                else:
                   print 'Fatal error! more that three dimension are not supported!'
                   print 'Potentially there are more than three nested loops!'
                   exit(-1)
            elif ndim==2:
                if blockDimx[1]==nesting:     
                    # parallelism at the same nesting 
                    print 'warning: overriding vector dim: '+blockDimx[0]+' with '+loopDim     
                    row={'blockDimx':[loopDim, nesting], 'blockDimy':blockDimy}
                else:
                    blockDimz=blockDimy
                    blockDimy=blockDimx
                    blockDimx=[loopDim, nesting]
                    row={'blockDimx':blockDimx, 'blockDimy':blockDimy, 'blockDimz':blockDimz}
            elif ndim==1:
                if blockDimx[1]==nesting:
                    # parallelism at the same nesting 
                    print 'warning: overriding vector dim: '+blockDimy[0]+' with '+blockDimx[0]
                    row={'blockDimx':[loopDim, nesting]}
                else:
                    blockDimy=blockDimx
                    blockDimx=[loopDim, nesting]
                    row={'blockDimx':blockDimx, 'blockDimy':blockDimy}
            else:
                print 'Fatal Error!'
                exit(-1)
            self.oacc_kernelsConfig[kernelId]=row
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

    def util_copyIdAppend(self, expressionIn, expressionAlloc, expressionOut, depth, expressionAll):
        #if expressionIn!='':
        #    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
        #    self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
        #    self.oacc_copys.append([self.oacc_kernelId,expressionIn])
        #    self.oacc_copyId=self.oacc_copyId+1
        ##   - create (allocation)
        #if expressionAlloc!='':
        #    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
        #    self.code=self.code+('\t'*depth)+self.prefix_datacp+str(self.oacc_copyId)+'();'
        #    self.oacc_copys.append([self.oacc_kernelId,expressionAlloc])
        #    self.oacc_copyId=self.oacc_copyId+1
        ##   - copy, copyout (allocation)
        #if expressionOut!='':
        #    self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
        #    copyoutId=self.oacc_copyId
        #    self.oacc_copys.append([self.oacc_kernelId,expressionOut])
        #    self.oacc_copyId=self.oacc_copyId+1
        if expressionAll=='':
            return -1
        else:
            self.code=self.code+('\t'*depth)+self.prefix_dataalloc+str(self.oacc_copyId)+'();'
            self.code=self.code+('\t'*depth)+self.prefix_datacpin+str(self.oacc_copyId)+'();'
            copyoutId=self.oacc_copyId
            self.oacc_copyId=self.oacc_copyId+1
            regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:/\+\^\|\&\(\)\*\ \[\]\.><-]*)(\")')
            d_copydetails = []
            for expr in expressionAll.split('\n'):
                dicent = {}
                for (a, b, c, d, e) in regex.findall(expr):
                    dicent[a] = d
                d_copydetails.append(dicent)
            self.oacc_copys.append([self.oacc_kernelId,d_copydetails])
            return copyoutId

    def oacc_data_dynamicAllowed(self, clause):
        clauses=['present', 'deviceptr']
        for c in clauses:
            if c==clause:
                return True
        return False

    def oacc_data_clauseparser(self, clause, type, inout, present, dID, isenter, isexit, compression):
        # parse openacc data clause and return correponding type (copyin, copyout, copy, pcopyin, pcopyout, pcopy, compression)
        code=''
        regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        #for i in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            if DEBUGVAR or DEBUGREGEX:
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
                    # compression
                    tcode=tcode+'compression="'+compression+'" '
                    # dimensions
                    #regex2 = re.compile(r'\[(.+?)\]')
                    #dims=regex2.findall(str(j).replace(' ',''))
                    dims=[j[1+j.find('['):j.rfind(']')]] #FIXME for multi-dimensional array it doesn't work
                    if DEBUGREGEX:
                        print 'regex> '+j+' '+'<>'.join(dims)
                    for dim in range(0,len(dims)):
                        if len(dims[dim].split(':')) > 2:
                            tcode=tcode+'min="'+dims[dim].split(':')[2]+'" '
                            tcode=tcode+'max="'+dims[dim].split(':')[3]+'" '
                            tcode=tcode+'dim'+str(dim)+'="'+dims[dim].split(':')[0]+':'+dims[dim].split(':')[1]+'" '
                        else:
                            tcode=tcode+'dim'+str(dim)+'="'+dims[dim]+'" '
                    tcode+='clause="'+type+'" '
                    tcode+='dataid="'+dID+'" '
                    tcode+='isenterdirective="'+('true' if isenter else 'false')+'" '
                    tcode+='isexitdirective="'+('true' if isexit else 'false')+'" '
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
            
    def oacc_clauseparser_data(self, clauses, dID, isenter, isexit):
        # isenter: true if it comes from pragma acc enter directive
        # isexit : true if it comes from pragma acc exit  directive
        expressionIn=''
        expressionAlloc=''
        expressionOut=''
        expressionAll=''
        # copy-in
        for it in ['copyin', 'copy']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','false', dID, isenter, isexit, 'false')
        for it in ['pcopy', 'present_or_copy', 'pcopyin', 'present_or_copyin']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','true', dID, isenter, isexit, 'false' )
        for it in ['ccopyin', 'ccopy', 'compression_copyin', 'compression_copy']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','false', dID, isenter, isexit, 'true')
        for it in ['pccopyin', 'pccopy', 'present_or_compression_copyin', 'present_or_compression_copy']:
            expressionIn=expressionIn+self.oacc_data_clauseparser(clauses,it,'true','true', dID, isenter, isexit, 'true')
        # allocate-only
        for it in ['create']:
            expressionAlloc=expressionAlloc+self.oacc_data_clauseparser(clauses,it,'create','true', dID, isenter, isexit, 'false')
        for it in ['ccreate', 'compression_create']:
            expressionAlloc=expressionAlloc+self.oacc_data_clauseparser(clauses,it,'create','true', dID, isenter, isexit, 'true')
        # copy-out
        for it in ['copyout', 'copy']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','false', dID, isenter, isexit, 'false')
        for it in ['pcopy', 'present_or_copy', 'pcopyout', 'present_or_copyout']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','true', dID, isenter, isexit, 'false')
        for it in ['ccopy', 'compression_copyin']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','false', dID, isenter, isexit, 'true')
        for it in ['pccopy', 'present_or_compression_copy']:
            expressionOut=expressionOut+self.oacc_data_clauseparser(clauses,it,'false','true', dID, isenter, isexit, 'true')
        for it in ['copy', 'pcopy', 'present_or_copy', 'copyout', 'pcopyout', 'present_or_copyout', 'copyin', 'pcopyin', 'present_or_copyin', 'create', 'present', 'present_or_create']:
            expressionAll=expressionAll+self.oacc_data_clauseparser(clauses,it,'false','false',dID, isenter, isexit, 'false')
        for it in ['ccopy', 'ccopyin', 'pccopy', 'pccopyin', 'compression_copy', 'compression_copyin', 'present_or_compression_copyin', 'present_or_compression_copy', 'ccreate', 'compression_create']:
            expressionAll=expressionAll+self.oacc_data_clauseparser(clauses,it,'false','false', dID, isenter, isexit, 'true')
        return [expressionIn, expressionAlloc, expressionOut, expressionAll]

    def oacc_clauseparser_data_ispresent(self, clause):
        for it in ['pcopy', 'present_or_copy', 'copyout', 'pcopyout', 'present_or_copyout', 'pcopyin', 'present_or_copyin', 'present', 'present_or_create', 'pccopy', 'pccopyin', 'present_or_compression_copyin', 'present_or_compression_copy']:
            if clause==it:
                return True
        return False


    def oacc_clauseparser_flags(self,clause,type):
        # parse openacc clause and return if type exists
        code=''
        regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        #regex = re.compile(r'([A-Za-z0-9\ ]+)\((.+?)\)')
        #for i in regex.findall(clause):
        for [i0, i1] in clauseDecomposer_break(clause):
            if DEBUGREGEX:
                print 'clauseparser-flags> '+i0+' '+i1
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

    def fix_call_args(self, kernelcode):
        cleanKerDec = kernelcode
        for [tmp_fname, tmp_prototype, tmp_declbody, tmp_rettype, tmp_qualifiers, tmp_params, tmp_local_vars, tmp_scope_vars, tmp_fcalls, tmp_ids, tmp_ex_params] in self.active_calls_decl:
            [params_t, params_v, params_s] = tmp_params
            [ex_params_t, ex_params_v, ex_params_s] = tmp_ex_params
            extra_params = [ex_params_v[idx] for idx in range(0,len(ex_params_t))]
            extra_args = (','.join(extra_params)+(',' if len(params_t)>0 else '')) if len(extra_params)>0 else ''
            #print extra_args
            cleanKerDec=re.sub('\\b'+tmp_fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+tmp_fname+'('+extra_args, cleanKerDec)
        return cleanKerDec

    def getAllFuncDecls(self):
        code=''
        for [fname, prototype, declbody, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in self.active_calls_decl:
            if self.target_platform=='ISPC':
                all_comb_params = self.getAllCombinationParams_ispc(params)
            else:
                all_comb_params = []
                all_comb_params.append(params)
            for new_params in all_comb_params:
                code += self.getSingleFuncProto(new_params, qualifiers, rettype, fname, ex_params, 'accel')+declbody[declbody.find('{'):]+'\n'
        # rename function calls within the declaration bodies
        for [fname, prototype, declbody, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in self.active_calls_decl:
            [ex_params_t, ex_params_v, ex_params_s] = ex_params
            [params_t, params_v, params_s] = params
            extra_params = [ex_params_v[idx] for idx in range(0,len(ex_params_t))]
            extra_args = (','.join(extra_params)+(',' if len(params_t)>0 else '')) if len(extra_params)>0 else ''
            code=re.sub('\\b'+fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+fname+'('+extra_args, code)
        # append new parameters
        return code

    def getAllFuncProto(self, proto_format):
        code=''
        for [fname, prototype, declbody, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in self.active_calls_decl:
            if self.target_platform=='ISPC' and proto_format=='accel':
                all_comb_params = self.getAllCombinationParams_ispc(params)
            else:
                all_comb_params = []
                all_comb_params.append(params)
            for new_params in all_comb_params:
                code += self.getSingleFuncProto(new_params, qualifiers, rettype, fname, ex_params, proto_format)+';\n'
        #self.getAllCombinationOfFuncProto_ispc( proto_format )
        return code

    def getAllCombinationOfFuncProto_ispc(self, proto_format):
        code = ''
        for [fname, prototype, declbody, rettype, qualifiers, params, local_vars, scope_vars, fcalls, ids, ex_params] in self.active_calls_decl:
            all_comb_params = self.getAllCombinationParams_ispc(params)
            for new_params in all_comb_params:
                print new_params
                code += self.getSingleFuncProto(new_params, qualifiers, rettype, fname, ex_params, proto_format)+';\n'
        print code

    def getAllCombinationParams_ispc(self, params):
        [params_t, params_v, params_s] = params
        all_comb_params = []
        all_comb_params.append(params)
        for idx in range(0,len(params_t)):
            if params_t[idx].find('*')!=-1:
                new_comb_params = []
                for listof_params in all_comb_params:
                    #print listof_params
                    [pt, pv, ps] = listof_params
                    # varying: not needed, it's the default
                    #new_pt = list(pt)
                    #new_pv = pv
                    #new_ps = ps
                    #new_pt[idx] = new_pt[idx]
                    ##new_pv[idx] = new_pv[idx]+('[]'*new_pt[idx].count('*'))
                    #new_comb_params.append([new_pt, new_pv, new_ps])
                    # uniform 
                    new_pt = list(pt)
                    new_pv = pv
                    new_ps = ps
                    new_pt[idx] = 'uniform '+new_pt[idx]
                    #new_pv[idx] = new_pv[idx]+('[]'*new_pt[idx].count('*'))
                    new_comb_params.append([new_pt, new_pv, new_ps])
                all_comb_params += new_comb_params
        return all_comb_params

    def getSingleFuncProto(self, params, qualifiers, rettype, fname, ex_params, proto_format):
        # proto_format: accel or host
        pointersprefix = ''
        if self.target_platform=='CUDA':
            requalified = ['__device__']
            for qf in qualifiers:
                if qf=='inline':
                    requalified.append('__inline__')
                # ignore rest of qualifiers: static, 
        elif self.target_platform=='OPENCL':
            requalified = []
            for qf in qualifiers:
                if qf=='inline':
                    requalified.append('__inline__')
                # ignore rest of qualifiers: static, 
            #print requalified
            pointersprefix = '__global ' # FIXME: not necessary for OpenCL >= 2.0 (enabled as a workaround for tests on NV OpenCL)
        elif self.target_platform=='ISPC':
            requalified = ['inline']+qualifiers
            #print requalified
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        requalified = list(set(requalified))
        [params_t, params_v, params_s] = params
        [ex_params_t, ex_params_v, ex_params_s] = ex_params
        extra_params = [(pointersprefix if ex_params_t[idx].find('*')!=-1 else '')+ex_params_t[idx]+' '+ex_params_v[idx] for idx in range(0,len(ex_params_t))]
        extra_args = ','.join(extra_params)+(',' if len(params_t)>0 else '') if len(extra_params)>0 else ''
        if self.target_platform=='ISPC':
            org_args = ', '.join([params_t[idx].replace('*','')+' '+params_v[idx]+('[]'*params_t[idx].count('*')) for idx in range(0,len(params_t))])
        else:
            org_args = ', '.join([(pointersprefix if params_t[idx].find('*')!=-1 else '')+params_t[idx]+' '+params_v[idx] for idx in range(0,len(params_t))])
        if fname in self.func_comp_vars:
            for compArgTuple in self.func_comp_vars[fname]:
                for arg in org_args:
                    if compArgTuple[0] == arg.strip().replace('*',' ').split()[1]:
                        org_args.append(arg.replace(compArgTuple[0],'__compress_constant_'+compArgTuple[0]))
        code = ' '.join(requalified)+' '+rettype+' __accelerator_'+fname+'('+extra_args+org_args+')'
        #fixme
        #for [funcName, prototype, declbody] in self.active_calls_decl:
        #    if funcName != fname:
        #        m=re.search(funcName+'\s*\((.*?)\)',code,re.S)
        #        if m:
        #            argList = m.group(1).split(',')
        #            if fname in self.func_comp_vars:
        #                for compVarTuple in self.func_comp_vars[fname]:
        #                    for arg in argList:
        #                        if arg.strip()==compVarTuple[0]:
        #                            #dummy=1
        #                            argList.append('__compress_constant_'+compVarTuple[0])
        #            comd=code.replace(m.group(0),funcName+'('+','.join(argList)+')')
        #    # Change compressed array accesses to macro [] => ()
        #if fname in self.func_comp_vars:
        #    for compArgTuple in self.func_comp_vars[fname]:
        #        var=compArgTuple[0]
        #        for arrayRef in re.finditer('\\b'+var+'[\\ \\t\\n\\r]*\[',code):
        #            arrayRef_it=arrayRef.start(0)
        #            arrayRef_pcnt=0
        #            done=False
        #            while not done:
        #                if code[arrayRef_it]=='[':
        #                    if arrayRef_pcnt==0:
        #                        #tempCode[arrayRef_it]='('
        #                        code=code[:arrayRef_it]+'('+code[arrayRef_it+1:]
        #                    arrayRef_pcnt+=1
        #                elif code[arrayRef_it]==']':
        #                    arrayRef_pcnt-=1
        #                    if arrayRef_pcnt==0:
        #                        #tempCode[arrayRef_it]=')'
        #                        code=code[:arrayRef_it]+')'+code[arrayRef_it+1:]
        #                        done=True
        #                arrayRef_it+=1
        ##code=re.sub('\\b'+fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+fname+'('+extra_args, code)
        return code

    # target platform code generators
    def codegen_includeHeaders(self):
        if self.target_platform=='CUDA':
            self.includeHeaders_cuda()
        elif self.target_platform=='OPENCL':
            self.includeHeaders_opencl()
        elif self.target_platform=='ISPC':
            self.includeHeaders_ispc()
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)  
            exit(-1)
    def codegen_syncDevice(self):
        if self.target_platform=='CUDA':
            return self.syncDevice_cuda()
        elif self.target_platform=='OPENCL':
            return self.syncDevice_opencl()
        elif self.target_platform=='ISPC':
            return '// ISPC target is synchronized with CPU\n// skipping synchronization\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_openCondition(self,cond):
        if self.target_platform=='CUDA':
            return self.openCondition_cuda(cond)
        elif self.target_platform=='OPENCL':
            return self.openCondition_opencl(cond)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_closeCondition(self,cond):
        if self.target_platform=='CUDA':
            return self.closeCondition_cuda(cond)
        elif self.target_platform=='OPENCL':
            return self.closeCondition_opencl(cond)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_reduceVariable(self, var, type, op, ctasize, nesteddepth):
        if int(nesteddepth)>0:
            print 'warning: reduction in this configuration is weakly supported!'
        if self.target_platform=='CUDA':
            return self.reduceVariable_cuda(var, type, op, ctasize, nesteddepth)
        elif self.target_platform=='OPENCL':
            return self.reduceVariable_opencl(var, type, op, ctasize, nesteddepth)
        else:
            return self.reduceVariable_ispc(var, type, op, ctasize, nesteddepth)
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_constructKernel(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, smcinfo, compInfo):
        if self.target_platform=='CUDA':
            return self.constructKernel_cuda(args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, self.oacc_kernelsTemplates[kernelId], smcinfo, compInfo)
        elif self.target_platform=='OPENCL':
            return self.constructKernel_opencl(args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, self.oacc_kernelsTemplates[kernelId], smcinfo, compInfo)
        elif self.target_platform=='ISPC':
            [a,b] = self.constructKernel_ispc(args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, self.oacc_kernelsTemplates[kernelId], smcinfo, compInfo)
            return [a,b]
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_appendKernelToCode(self, kerPro, kerDec, kerId, forDims, args, smcinfo):
        if self.target_platform=='CUDA':
            self.appendKernelToCode_cuda(kerPro, kerDec, kerId, forDims, args)
        elif self.target_platform=='OPENCL':
            self.appendKernelToCode_opencl(kerPro, kerDec, kerId, forDims, args, smcinfo)
        elif self.target_platform=='ISPC':
            self.appendKernelToCode_ispc(kerPro, kerDec, kerId, forDims, args, smcinfo)
            #print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            #exit(-1)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_memAlloc(self, dvar, size, hvar, type, scalar_copy, ispresent, pseudotp, compression, min, max):
        amp=('&' if scalar_copy else '')
        isRangeGiven=not (min=='' or max=='')
        fcall='acc_'+('compress_' if compression=='true' else '')+('present_or_' if ispresent else '')+'create'
        if compression == 'true':
            self.oacc_constCoefDefs+="__constant__ "+type.replace('*','').strip()+' __compress_constant_main_'+hvar+'[10];\n'
        if self.target_platform=='CUDA' or self.target_platform=='OPENCL':
            if pseudotp=='': #TODO Integrating pseudotp with compression.
                #code=fcall+'((void*)'+amp+hvar+','+size+');\n'# Before adding compressoin feature.
                code=fcall+'((void*)'+amp+hvar+','+size+((', "'+type.replace('*','').strip()+'", '+'__compress_constant_main_'+hvar+', '+('0' if isRangeGiven else '1')+', '+(min if isRangeGiven else '0' )+', '+ (max if isRangeGiven else '0')) if compression=='true' else '')+');\n'
            else:
                code=fcall+'((void*)__ipmacc_contmap.addmap('+hvar+'),'+size+');\n'
        elif self.target_platform=='ISPC':
            code='// ISPC host and device are the same, skipping memory allocation\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        return code

    def codegen_accDevicePtr(self, dvar, size, hvar, type, scalar_copy):
        code=''
        if self.target_platform=='CUDA':
            code+=dvar+'=('+type+')acc_deviceptr((void*)'+('&'if scalar_copy else '')+hvar+');\n'
        elif self.target_platform=='OPENCL':
            code+=dvar+'=(cl_mem)acc_deviceptr((void*)'+('&'if scalar_copy else '')+hvar+');\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        return code

    def codegen_accCopyin(self, host, dev, bytes, type, present, scalar_copy, pseudotp):
        ast=('*' if scalar_copy else '')
        code=''
        if self.target_platform=='CUDA' or self.target_platform=='OPENCL':
            if pseudotp=='':
                code+='acc_'+present+'copyin((void*)'+host+','+bytes+');\n'
            else:
                code+='acc_'+present+'copyin((void*)__ipmacc_contmap.copyin('+host+'),'+bytes+');\n'
        elif self.target_platform=='ISPC':
            code='// ISPC host and device are the same, skipping copyin\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        return code

    def codegen_accCompCopyin(self, host, dev, bytes, type, present, scalar_copy, parentFunc,min,max):
        ast=('*' if scalar_copy else '')
        code=''
        isRangeGiven=not (min=='' or max=='')
        if self.target_platform=='CUDA':
            # TODO code+=dev+'=('+type+ast+')acc_'+present+'copyin((void*)'+host+','+bytes+');\n'
            code+='acc_'+present+'compress_copyin((void*)'+host+','+bytes+', "'+type.replace('*','').strip()+'", __compress_constant_main_'+host+', '+('0' if isRangeGiven else '1')+', '+(min if isRangeGiven else '0' )+', '+ (max if isRangeGiven else '0')+'); // '+type+'\n'
            #self.oacc_constCoefDefs+="__constant__ "+type.replace('*','').strip()+' __compress_constant_main_'+host+'[10];\n'
            #print self.code
        elif self.target_platform=='OPENCL':
            # code+=dev+'=(cl_mem)acc_'+present+'copyin((void*)'+host+','+bytes+');\n'
            code+='acc_'+present+'compress_copyin((void*)'+host+','+bytes+');\n'
        else:
            print 'error: unimplemented platform'
            exit(-1)
        return code

    def codegen_accPresent(self, host, dev, bytes, type):
        code=''
        if self.target_platform=='CUDA' or self.target_platform=='OPENCL':
            code+='acc_present((void*)'+host+');\n'
        elif self.target_platform=='ISPC':
            code+='// skipping acc_present on ISPC\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        return code

    def codegen_accPCopyout(self, host, dev, bytes, type, scalar_copy, pseudotp):
        ast=('*' if scalar_copy else '')
        code=''
        if self.target_platform=='CUDA' or self.target_platform=='OPENCL':
            if pseudotp=='':
                code+='acc_copyout_and_keep((void*)'+host+','+bytes+');\n'
            else:
                code+='acc_copyout_and_keep((void*)__ipmacc_contmap.get_buffer_ptr('+host+'),'+bytes+');\n'
                code+='__ipmacc_contmap.copyout('+host+');\n'
        elif self.target_platform=='ISPC':
            code='// ISPC host and device are the same, skipping copyout\n'
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
        return code

    def codegen_accPCompCopyout(self, host, dev, bytes, type, scalar_copy, parentFunc):
        ast=('*' if scalar_copy else '')
        code=''
        if self.target_platform=='CUDA' or self.target_platform=='OPENCL':
            code+='acc_decompress_copyout((void*)'+host+','+bytes+');\n'
        else:
            print 'error: unimplemented platform'
            exit(-1)
        return code
 
    def codegen_memCpy(self, des, src, size, type):
        if self.target_platform=='CUDA':
            return self.memCpy_cuda(des, src, size, type)
        elif self.target_platform=='OPENCL':
            return self.memCpy_opencl(des, src, size, type)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_devPtrDeclare(self, type, name, sccopy):
        # sccopy stands for scalar explicit copy
        if self.target_platform=='CUDA':
            return self.devPtrDeclare_cuda(type, name, sccopy)
        elif self.target_platform=='OPENCL':
            return self.devPtrDeclare_opencl(type, name, sccopy)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_getFuncProto(self, proto_format):
        # return prototype/declarations
        return self.getAllFuncProto(proto_format)
    def codegen_getFuncDecls(self):
        # return prototype/declarations
        return self.getAllFuncDecls()
    def codegen_getTypeFwrDecl(self):
        # return prototype/declarations
        if self.target_platform=='CUDA':
            return self.getTypeFwrDecl_cuda()
        elif self.target_platform=='OPENCL':
            return self.getTypeFwrDecl_opencl()
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)

    def codegen_renameStadardTypes(self):
        # replace the types which are conflicting with cuda built-in types
        if self.target_platform=='CUDA':
            for tp in self.intrinsic_types_cuda:
                self.code = re.sub('\\b'+tp+'\\b','__ipmacc_'+tp, self.code)
        elif self.target_platform=='OPENCL':
            #nop=True
            for tp in self.intrinsic_types_ocl:
                self.code = re.sub('\\b'+tp+'\\b','__ipmacc_'+tp, self.code)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_renameStadardCalls(self):
        # replace the types which are conflicting with cuda built-in types
        if self.target_platform=='CUDA':
            nop=True
        elif self.target_platform=='OPENCL':
            callsToRename=['rsqrtf'] # list of calls to rename withing the kernel
            callsToReplace=['rsqrt'] # list of calls to replace them
            for idx in range(0,len(callsToRename)):
                tp=callsToRename[idx]
                self.code = re.sub('\\b'+tp+'\\b', callsToReplace[idx], self.code)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)
    def codegen_generate_algorithm(self, clauses):
        #clauseDecomposer_break
        if self.target_platform=='CUDA':
            return clauseDecomposer_break(clauses)
        #elif self.target_platform=='OPENCL':
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)

    def codegen_atomic(self, atomicBody, atomicClause, kernelId, lockindex):
        if self.target_platform=='CUDA':
            return self.atomic_cuda(atomicBody, atomicClause, kernelId, lockindex)
        elif self.target_platform=='OPENCL':
            return self.atomic_opencl(atomicBody, atomicClause, kernelId, lockindex)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)

    def codegen_algo(self, algoBody, algoClause, kernelId, revdepnest):
        if self.target_platform=='CUDA':
            return self.algo_cuda(algoBody, algoClause, kernelId, revdepnest)
        #elif self.target_platform=='OPENCL':
        #    return self.algo_opencl(atomicBody, atomicClause, kernelId)
        else:
            print 'error: unimplemented platform #' +str(getframeinfo(currentframe()).lineno)
            exit(-1)

    # cuda platform
    def includeHeaders_cuda(self):
        self.code_include+='#include <cuda.h>\n'
        if len(self.oacc_algoReg)>0:
            self.code_include+='#include "openacc_algo.cu"\n'
    def initDevice_cuda(self):
        return ''
    def syncDevice_cuda(self):
        code=''
        code+='if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\\n");\n'
        if PROFILER:
            code+='acc_profiler_start();\n'
        code+='{\ncudaError err=cudaDeviceSynchronize();\nif(err!=cudaSuccess){\nprintf("Kernel Launch Error! error code (%d)\\n",err);\nassert(0&&"Launch Failure!\\n");}\n}\n'
        if PROFILER:
            code+='acc_profiler_end(1);\n'
        return code
    def openCondition_cuda(self,cond):
        return 'if('+cond+'){\n'
    def closeCondition_cuda(self,cond):
        return '}\n'
    def appendKernelToCode_cuda(self, kerPro, kerDec, kerId, forDims, args):
        self.code=self.code.replace(' __ipmacc_prototypes_kernels_'+str(kerId)+' ',' '+self.codegen_getFuncProto('host')+kerPro+' \n')
        #self.cuda_kernelproto+=kerPro
        self.cuda_kerneldecl +=kerDec
        [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kerId)
        args_last_grid_details = []
        if nctadim>1 or GENMULTIDIMTB:
            if DEBUGMULTIDIMTB:
                print 'injecting thread-block code:'
            dim3_gridblock= 'dim3 __ipmacc_gridDim(1,1,1);\n'
            dim3_gridblock+='dim3 __ipmacc_blockDim(1,1,1);\n'
            for f in range(0,len(forDims)):
                if forDims[f]=='':
                    break
                if   f==0:
                    ch='x'
                    dimension=ctadimx
                elif f==1:
                    ch='y'
                    dimension=ctadimy
                elif f==2:
                    ch='z'
                    dimension=ctadimz
                else:
                    print 'Error! Multi-dimensional grid is limited up to 3. Disable GENMULTIDIMTB in condegen.py'
                    exit(-1)
                #print ch+' '+dimension+' '+str(f)+' '+forDims[f]+' '+str(len(forDims))
                dim3_gridblock+='__ipmacc_blockDim.'+ch+'='+dimension+';\n'
                #dim3_gridblock+='__ipmacc_blockDim.'+ch+'='+self.blockDim_cuda_xyz+';\n'
                padgrid='(((int)ceil('+forDims[f]+')%('+dimension+'))==0?0:1)'
                dim3_gridblock+='__ipmacc_gridDim.'+ch+'=(('+forDims[f]+')/__ipmacc_blockDim.'+ch+')+('+padgrid+');\n'
                args_last_grid_details.append('\n((int)'+forDims[f]+')%('+dimension+')==0?'+dimension+':((int)'+forDims[f]+')%('+dimension+')')
            if DEBUGMULTIDIMTB:
                print dim3_gridblock
        else:
            blockDim=ctadimx #self.blockDim_cuda
            padgrid='(((int)ceil('+forDims+')%('+blockDim+'))==0?0:1)'
            gridDim='('+forDims+')/'+blockDim+'+'+padgrid
            args_last_grid_details.append('\n((int)'+forDims+')%('+blockDim+')==0?'+blockDim+':((int)'+forDims+')%('+blockDim+')')

        callArgs=[]
        atomicRegion=False
        for i in args:
            argName=i.split(' ')
            argType=''
            if i.find(self.prefix_kernel_atomicLocks)!=-1:
                if DEBUGATOMIC: print 'atomic variable: '+i
                atomicRegion=True
            #for singleArg in argName:
            #    if singleArg!='static':
            #        argType+=singleArg+' '
            argType=' '.join(argName[0:len(argName)-1])
            argName=argName[len(argName)-1]
            if argName.find('__ipmacc_scalar')!=-1:
                argName='&'+argName.replace('__ipmacc_scalar','')
            if argName.find('__ipmacc_reductionarray_internal')!=-1:
                argName=self.prefix_kernel_reduction_array+argName
                argName=argName.replace('__ipmacc_reductionarray_internal','')
            #TODO callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName, self.oacc_kernelsAssociatedCopyIds[kerId]))
            argName=argName.replace('__ipmacc_opt_readonlycache','')
            if argName.find('__ipmacc_container')!=-1:
                argName=argName.replace('__ipmacc_container','')
                callArgs.append( ('\n('+argType+')acc_deviceptr((void*)__ipmacc_contmap.get_buffer_ptr('+argName+'))') )
            elif argName.find('__ipmacc_deviceptr')!=-1:
                argName=argName.replace('__ipmacc_deviceptr','')
                callArgs.append( '\n'+argName)
            else:
                callArgs.append( ('\n('+argType+')acc_deviceptr((void*)'+argName+')') if argType.find('*')!=-1 else '\n'+argName)

        if CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD==CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_ARG:
            for i in range(len(args_last_grid_details),3):
                args_last_grid_details.append('\n1')
            callArgs+=args_last_grid_details

        kernelInvoc='\n/* kernel call statement '+str(self.oacc_kernelsAssociatedCopyIds[kerId])+'*/\n{\n'
        if atomicRegion:
            if DEBUGATOMIC: print 'atomic found!'
            atomicCodePreKernel=self.atomicRegion_locktype+' '+self.prefix_kernel_atomicLocks+'['+str(self.atomicRegion_nlocks)+']={'+', '.join('0'*self.atomicRegion_nlocks)+'};\n'
            atomicCodePreKernel+='acc_pcopyin((void*)'+self.prefix_kernel_atomicLocks+',10*sizeof('+self.atomicRegion_locktype+'));\n'
            atomicCodePostKernel=''
        else:
            atomicCodePreKernel=''
            atomicCodePostKernel=''
        if nctadim>1 or GENMULTIDIMTB:
            dynamic_shared_memory_size = '0' if len(self.cuda_shared_memory_dynamic_alloc)==0 else '(' + ')*('.join(self.cuda_shared_memory_dynamic_alloc) + ')'
            dynamic_shared_memory_size = dynamic_shared_memory_size.replace('blockDim', '__ipmacc_blockDim') # These lines were written at Euro 2016, Portugal vs Poland; sry for inconvenience
            kernelInvoc+=dim3_gridblock
            kernelInvoc+='if (getenv("IPMACC_VERBOSE")){\nprintf("IPMACC: Launching kernel '+str(kerId)+' > gridDim: (%u,%u,%u)\\tblockDim: (%u,%u,%u) shared memory size (bytes): %d\\n",__ipmacc_gridDim.x,__ipmacc_gridDim.y,__ipmacc_gridDim.z,__ipmacc_blockDim.x,__ipmacc_blockDim.y,__ipmacc_blockDim.z, '+dynamic_shared_memory_size+');\n}\n'
            if PROFILER:
                kernelInvoc+='acc_profiler_start();\n'
            kernelInvoc += self.perforation_gen_expansion(kerId)
            kernelInvoc+=self.prefix_kernel_gen+str(kerId)+('_compression' if len(self.oacc_kernelsComp[kerId])!=0 else '')+'<<<__ipmacc_gridDim,__ipmacc_blockDim,'+ dynamic_shared_memory_size +'>>>('+(','.join(callArgs))+');'
            if PROFILER:
                kernelInvoc+='acc_profiler_end(0);\n'
        else:
            kernelInvoc+='int griddim_x = '+gridDim+';\n'
            kernelInvoc+=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel '+str(kerId)+' > gridDim: %d\\tblockDim: %d\\n", griddim_x, '+blockDim+');\n')
            if PROFILER:
                kernelInvoc+='acc_profiler_start();\n'
            if len(self.oacc_algoReg)!=0:
                print 'fatal error: single dimensional thread blocks are used within algorithm directive.'
                exit(-1)
            dynamic_shared_memory_size = '0' 
            #dynamic_shared_memory_size = '0' if len(self.cuda_shared_memory_dynamic_alloc)==0 else '(' + ')*('.join(self.cuda_shared_memory_dynamic_alloc) + ')'
            #dynamic_shared_memory_size = dynamic_shared_memory_size.replace('blockDim', blockDim)
            kernelInvoc += self.perforation_gen_expansion(kerId)
            kernelInvoc+=self.prefix_kernel_gen+str(kerId)+('_compression' if len(self.oacc_kernelsComp[kerId])!=0 else '')+'<<< griddim_x, '+blockDim+', '+dynamic_shared_memory_size+'>>>('+(','.join(callArgs))+');'
            if PROFILER:
                kernelInvoc+='acc_profiler_end(0);\n'
        kernelInvoc+='\n}\n/* kernel call statement*/\n'
        self.code=self.code.replace(self.prefix_kernel+str(kerId)+'();',atomicCodePreKernel+kernelInvoc+atomicCodePostKernel)
    def reduceVariable_cuda(self, var, type, op, ctasize, nesteddepth):
        # ctasize: list of dimensions of thread block
        # nesteddepth: 0 for most outer, 1 for the immediate, and so on
        arrname=self.prefix_kernel_reduction_shmem+var
        iterator=self.prefix_kernel_reduction_iterator
        code ='\n/* reduction on '+var+' */\n'
        code+="""int __ctadimx=blockDim.x;
               if(blockIdx.x==(gridDim.x-1)){
                   __shared__ bool flag;
                   int begin=0, end=blockDim.x;
                   while(true){
                       int newend = (end+begin)>>1;
                       __syncthreads();
                       flag=false;
                       __syncthreads();
                       if(threadIdx.x>=newend)
                           flag=true;
                       __syncthreads();
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimx=begin+1;
                           break;
                       }
                   }
               }
               int __ctadimy=blockDim.y;
               if(blockIdx.y==(gridDim.y-1)){
                   __shared__ bool flag;
                   int begin=0, end=blockDim.y;
                   while(true){
                       int newend = (end+begin)>>1;
                       __syncthreads();
                       flag=false;
                       __syncthreads();
                       if(threadIdx.y>=newend)
                           flag=true;
                       __syncthreads();
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimy=begin+1;
                           break;
                       }
                   }
               }
               int __ctadimz=blockDim.z;
               if(blockIdx.z==(gridDim.z-1)){
                   __shared__ bool flag;
                   int begin=0, end=blockDim.z;
                   while(true){
                       int newend = (end+begin)>>1;
                       __syncthreads();
                       flag=false;
                       __syncthreads();
                       if(threadIdx.z>=newend)
                           flag=true;
                       __syncthreads();
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimz=begin+1;
                           break;
                       }
                   }
               }\n"""
        code+='__syncthreads();\n'
        #code+='unsigned int uniqueflat_local_id=threadIdx.x+threadIdx.y*(blockDim.x)+threadIdx.z*(blockDim.x*blockDim.y);\n'
        if nesteddepth=='0':
            code+='unsigned int uniqueflat_local_id=threadIdx.x+threadIdx.y*(__ctadimx)+threadIdx.z*(__ctadimx*__ctadimy);\n'
            code+=arrname+'[uniqueflat_local_id]='+var+';\n';
        elif nesteddepth=='1':
            code+='unsigned int uniquerow_local_id=threadIdx.z;\n'
            code+='unsigned int uniquecol_local_id=threadIdx.x+threadIdx.y*(__ctadimx);\n'
            code+=arrname+'[uniquerow_local_id][uniquecol_local_id]='+var+';\n';
        elif nesteddepth=='2':
            code+='unsigned int uniquerow_local_id=threadIdx.y+threadIdx.z*(__ctadimy);\n'
            code+='unsigned int uniquecol_local_id=threadIdx.x;\n'
            code+=arrname+'[uniquerow_local_id][uniquecol_local_id]='+var+';\n';
        else:
            print 'unsupported reduction configuration!'
            exit(-1)
        code+='//printf("%dx%dx%d %dx%dx%d %d\\n",blockIdx.x,blockIdx.y,blockIdx.z,__ctadimx,__ctadimy,__ctadimz,uniqueflat_local_id);\n'
        code+='__syncthreads();\n'

        # ALTERED BEGIN
        # ALTER 1 
        #code+='for('+iterator+'='+ctasize+'; '+iterator+'>1; '+iterator+'='+iterator+'/2){\n'
        #code+='if(threadIdx.x<'+iterator+' && threadIdx.x>='+iterator+'/2){\n'
        #des=arrname+'[threadIdx.x-('+iterator+'/2)]'
        #src=arrname+'[threadIdx.x]'
        #if op=='min':
        #    code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        #elif op=='max':
        #    code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        #else:
        #    code+=des+'='+des+op+src+';\n'
        #code+='}\n'
        #code+='__syncthreads();\n'
        #code+='}\n'
        # ALTER 2 
        #code+='for('+iterator+'=(blockDim.x*blockDim.y*blockDim.z)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
        if nesteddepth=='0':
            src=arrname+'[uniqueflat_local_id+'+iterator+']'
            des=arrname+'[uniqueflat_local_id]'
            code+='unsigned int reduction_length=__ctadimx*__ctadimy*__ctadimz;\n'
            code+='unsigned int startpoint=1<<(32-__clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(uniqueflat_local_id<'+iterator+' && (uniqueflat_local_id+'+iterator+')<reduction_length){\n'
        elif nesteddepth=='1':
            src=arrname+'[rowid][colid+'+iterator+']'
            des=arrname+'[rowid][colid]'
            code+='unsigned int nrows=__ctadimz;\n'
            code+='unsigned int ncols=__ctadimx*__ctadimy;\n'
            code+='unsigned int colid=threadIdx.x+threadIdx.y*__ctadimx;\n'
            code+='unsigned int rowid=threadIdx.z;\n'
            code+='unsigned int reduction_length=ncols;\n'
            code+='unsigned int startpoint=1<<(32-__clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(colid<'+iterator+' && (colid+'+iterator+')<reduction_length && colid<ncols && rowid<nrows){\n'
        elif nesteddepth=='2':
            src=arrname+'[rowid][colid+'+iterator+']'
            des=arrname+'[rowid][colid]'
            code+='unsigned int nrows=__ctadimz*__ctadimy;\n'
            code+='unsigned int ncols=__ctadimx;\n'
            code+='unsigned int colid=threadIdx.x;\n'
            code+='unsigned int rowid=threadIdx.y+threadIdx.z*__ctadimy;\n'
            code+='unsigned int reduction_length=ncols;\n'
            code+='unsigned int startpoint=1<<(32-__clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(colid<'+iterator+' && (colid+'+iterator+')<reduction_length && colid<ncols && rowid<nrows){\n'
        else:
            print 'unsupported reduction configuration!'
            exit(-1)
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+='}\n'
        code+='__syncthreads();\n'
        code+='}\n'
        # END OF ALTER

        code+='}// the end of '+var+' scope\n'
        code+='/* distribute the local reduction results to threads */\n'
        if   nesteddepth=='0':
            code+=var+'='+arrname+'[0];\n'
        elif nesteddepth=='1':
            code+='unsigned int rowid=threadIdx.z;\n'
            code+=var+'='+arrname+'[rowid][0];\n'
        elif nesteddepth=='2':
            code+='unsigned int rowid=threadIdx.y+threadIdx.z*__ctadimy;\n'
            code+=var+'='+arrname+'[rowid][0];\n'
        code+='/* write intermediate result back */\n'
        code+='if(threadIdx.x==0 && threadIdx.y==0 && threadIdx.z==0){\n'
        if REDUCTION_TWOLEVELTREE:
            if nesteddepth=='0':
                code+=var+'__ipmacc_reductionarray_internal[blockIdx.x+blockIdx.y*(gridDim.x)+blockIdx.z*(gridDim.x*gridDim.y)]='+arrname+'[0];\n'
            else:
                code+=var+'__ipmacc_reductionarray_internal[blockIdx.x+blockIdx.y*(gridDim.x)+blockIdx.z*(gridDim.x*gridDim.y)]='+arrname+'[0][0];\n'
        else:
            self.code_include+='__device__ unsigned long long int '+self.prefix_kernel_reduction_lock+var+'=0u;\n'
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



    def constructKernel_cuda(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, template, smcinfo, compInfo):
        [nctadim, ctadimx, ctadimy, ctadimz]=ctasize
        # append SMC arguments
        args_extra = []
        if CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD==CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_ARG:
            for ch in ['x', 'y', 'z']:
                args_extra.append('unsigned int __ipmacc_last_blockdim_'+ch)
        ############ After adding compression
        compCodeInit=''
        simpleCodeInit=''
        code=''
        proto=''
        coefArgs=[]
        if len(self.oacc_kernelsComp[kernelId])!=0:
            for compVarObj in self.oacc_kernelsComp[kernelId]:
                for arg in args:
                    if arg.replace('*',' ').split()[-1].replace('__ipmacc_deviceptr','').replace('__ipmacc_opt_readonlycache','')==str(compVarObj.varName):
                        coefArgs.append(('__compress_constant_'+str(compVarObj.varName)).join(arg.rsplit(str(compVarObj.varName),1)))
                        compCodeInit+='#define '+str(compVarObj.varName)+'(index) decompress_'+arg.replace('*',' ').split()[0]+'((void*)'+str(compVarObj.varName)+', index, __compress_constant_main_'+str(compVarObj.varName)+')\n'
                        print 'warning: might not work if', arg, 'type is greater than one word.'
                        compVarObj.type=arg.replace('*',' ').split()[0]
            compCodeInit+=template+' __global__ void '+self.prefix_kernel_gen+str(kernelId)+'_compression'
            #compCodeInit+='('+(','.join(args+coefArgs)).replace('__ipmacc_deviceptr','')+')'
            if self.opt_readonlycache:
                compCodeInit+='('+(','.join(args)).replace('__ipmacc_deviceptr','')+')'
            else:
                compCodeInit+='('+(','.join(args)).replace('__ipmacc_deviceptr','').replace('__ipmacc_opt_readonlycache','')+')'
            proto+=template+' __global__ void '+self.prefix_kernel_gen+str(kernelId)+'_compression'
            if self.opt_readonlycache:
                proto+='('+(','.join(args)).replace('__ipmacc_deviceptr','')+');'
            else:
                proto+='('+(','.join(args)).replace('__ipmacc_deviceptr','').replace('__ipmacc_opt_readonlycache','')+');'
            #proto+='('+(','.join(args+coefArgs)).replace('__ipmacc_deviceptr','')+');'
            #proto+='('+(','.join(args)).replace('__ipmacc_deviceptr','')+');'
        simpleCodeInit+=template+' __global__ void '+self.prefix_kernel_gen+str(kernelId)
        #print "lashgar goft:"+simpleCodeInit
        #simpleCodeInit+='('+(','.join(args)).replace('__ipmacc_deviceptr','')+')'
        if self.opt_readonlycache:
            simpleCodeInit+='('+(','.join(args+args_extra)).replace('__ipmacc_deviceptr','').replace('__ipmacc_container','')+')'
        else:
            simpleCodeInit+='('+(','.join(args+args_extra)).replace('__ipmacc_deviceptr','').replace('__ipmacc_container','').replace('__ipmacc_opt_readonlycache','')+')'
        proto+='\n'+simpleCodeInit+';\n\n'
        #################

	############# Before adding compression
        #code=template+' __global__ void '+self.prefix_kernel_gen+str(kernelId)
        #if self.opt_readonlycache:
        #    code=code+'('+(','.join(args)).replace('__ipmacc_deviceptr','').replace('__ipmacc_container','')+')'
        #else:
        #    code=code+'('+(','.join(args)).replace('__ipmacc_deviceptr','').replace('__ipmacc_container','').replace('__ipmacc_opt_readonlycache','')+')'
        #proto=code+';\n'
	##############
        code+='{\n'
        code+='int '+self.prefix_kernel_uid_x+'=threadIdx.x+blockIdx.x*blockDim.x;\n'
        code+='int '+self.prefix_kernel_uid_y+'=threadIdx.y+blockIdx.y*blockDim.y;\n'
        code+='int '+self.prefix_kernel_uid_z+'=threadIdx.z+blockIdx.z*blockDim.z;\n'
        if self.opt_readonlycache:
            for vname in args:
                if vname.find('__ipmacc_opt_readonlycache')!=-1:
                    code+=vname.replace('__ipmacc_opt_readonlycache',' const __restrict__ ')+' = '+ vname.split()[-1] + ';\n'
        # fetch __ipmacc_scalar into register
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                s_type=sc.replace(vname,'').replace('*','')
                code+=s_type+' '+vname.replace('__ipmacc_scalar','')+' = '+vname+'[0];\n'
                code+='bool '+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard = false;\n'
        #code+='if('+self.prefix_kernel_uid_x+'>='+forDims+'){\nreturn;\n}\n'
        if len(reduinfo+privinfo)>0:
            # 1) serve privates
            pfreelist=[]
            for [v, i, o, a, t, d] in privinfo:
                if t.find('*')!=-1:
                    print 'subarray in private clause is not supported:', t, v
                    print 'aborting()'
                    exit(-1)
                fcall=self.prefix_kernel_privred_region+str(a)+'();'
                scp=('{ //start of reduction region for '+v+' \n') if o!='U' else ''
                kernelB=kernelB.replace(fcall,scp+t+' '+v+'='+i+';\n'+fcall)
                pfreelist.append(a)
            for ids in pfreelist:
                fcall=self.prefix_kernel_privred_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'');
            # 2) serve reductions
            decl+='int '+self.prefix_kernel_reduction_iterator+'=0;\n'
            types=[] # unique pair of types-depth to reserve space for fast shared-memory reductions
            rfreelist=[] #remove reduction calls
            reduinfo.reverse()
            for [v, i, o, a, t, depth] in reduinfo:
                fcall=self.prefix_kernel_reduction_region+str(a)+'();'
                # 2) 1) append proper reduction code for this variable
                kernelB=kernelB.replace(fcall,self.codegen_reduceVariable(v,t,o,ctasize,depth)+fcall)
                types.append(t+depth)
                rfreelist.append(a)
                decl+=t+' '+v+';'
            reduinfo.reverse()
            # 2) 2) allocate shared memory reduction array
            types=list(set(types))
            #for t in types:
            for [v, i, o, a, t, depth] in reduinfo:
                #depth=t[-1]
                neutralvalue=self.get_neutralValueForOperation(o)
                if not(ctadimx.isdigit() and ctadimy.isdigit() and ctadimz.isdigit()):
                    print 'error: thread block dimension should be fixed for reduction!\n\tuse vector clause over loop directives to fix it.'
                    exit(-1)
                if depth=='0':
                    code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimx,ctadimy,ctadimz])+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[threadIdx.x+threadIdx.y*blockDim.x+threadIdx.z*(blockDim.x*blockDim.y)]='+neutralvalue+';\n'
                    code+='__syncthreads();\n'
                elif depth=='1':
                    code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+ctadimz+']['+'*'.join([ctadimx,ctadimy])+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[threadIdx.z][threadIdx.x+threadIdx.y*blockDim.x]='+neutralvalue+';\n'
                    code+='__syncthreads();\n'
                elif depth=='2':
                    code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimy,ctadimz])+']['+ctadimx+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[threadIdx.y+threadIdx.z*blockDim.y][threadIdx.x]='+neutralvalue+';\n'
                    code+='__syncthreads();\n'
                else:
                    print 'unsupported reduction configuration!'
            rfreelist=list(set(rfreelist))
            # 2) 3) free remaining fcalls
            for ids in rfreelist:
                fcall=self.prefix_kernel_reduction_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'')

        # ATOMIC OPERATIONS
        atomicBlocks=[]
        for [atomicKId, atomicId, atomicBody, atomicClause] in self.oacc_atomicReg:
            if atomicKId == kernelId:
                atomicBlocks.append([atomicId, atomicBody, atomicClause])
        if len(atomicBlocks)>0:
            lockindex=0
            for [atomicId, atomicBody, atomicClause] in atomicBlocks:
                #kernelB=kernelB.replace(self.prefix_kernel_atomicRegion+str(atomicId)+'();','/*\n'+atomicBody+'\n*/\n')
                kernelB=kernelB.replace(self.prefix_kernel_atomicRegion+str(atomicId)+'();\n'+atomicBody,'\n'+self.codegen_atomic(atomicBody, atomicClause, kernelId, lockindex)+'\n\n')
                lockindex+=1

        # ALGORITHM OPERATIONS
        algoBlocks=[]
        for [algoKId, algoId, algoBody, algoClause, revdepnest] in self.oacc_algoReg:
            if algoKId == kernelId:
                algoBlocks.append([algoId, algoBody, algoClause, revdepnest])
        if len(algoBlocks)>0:
            for [algoId, algoBody, algoClause, revdepnest] in algoBlocks:
                [algoDecl, algoCall] = self.codegen_algo(algoBody, algoClause, kernelId, revdepnest)
                kernelB=kernelB.replace(self.prefix_kernel_algoRegion+str(algoId)+'();\n'+algoBody,'\n'+algoCall+'\n\n')
                decl += algoDecl

        smc_select_calls=''
        smc_write_calls=''
        if len(smcinfo)>0:
            if DEBUGSMC: print 'found smc clause'
            pfreelist=[]
            fusionSMC=[]
            for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up, dim2low, dim2high, pivot2, dw2range, up2range, w_dw2range, w_up2range, vcode] in smcinfo:

                if DEBUGSMC:
                    self.debug_dump_smcInfo([[v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up, dim2low, dim2high, pivot2, dw2range, up2range, w_dw2range, w_up2range, vcode]])
                # skip if the pivot is not in the normal form or
                # the directive is called from a `potentially' divergent path
                fcall=self.prefix_kernel_smc_fetch+str(a)+'();'
                if (not (self.smc_cache_base_is_normal(p, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB) and\
                         self.smc_cache_base_is_normal(pivot2, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB)))\
                        or self.smc_cache_is_divergent(fcall, kernelB):
                    fcallst=self.prefix_kernel_smc_fetch+str(a)+'();'
                    fcallen=self.prefix_kernel_smc_fetchend+str(a)+'();'
                    kernelB = kernelB.replace(fcallst,'').replace(fcallen,'')
                    print 'warning: skipping cache directive;', 'cannot perform effective optimizations.'
                    continue

                # try:
                #     tagbasedcache_size = str(int(div.replace('tag','')))
                #     tagbasedcache_datp = ' int '
                # except:
                #     tagbasedcache_size = ''
                #     tagbasedcache_datp = ' int '

                # can it be merged with previous smc code?
                isfusion=False
                fusionIdx=-1
                for fid in range(0,len(fusionSMC)):
                    [tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7]=fusionSMC[fid]
                    if tmp1==p and tmp2==dw and tmp3==up and tmp4==pivot2 and tmp5==dw2range and tmp6==up2range:
                        isfusion=True
                        fusionIdx=fid
                        break
                if not isfusion:
                    fusionSMC.append([p, dw, up, pivot2, dw2range, up2range, v])
                if kernelB.find(fcall)==-1:
                    # this smc does not belong to this kernel, ignore 
                    if DEBUGSMC: print 'skip> '+fcall
                    continue
                if dim2high=='' and dim2low=='':
                    # for 1D SMC
                    [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kernelId)
                    [f_is_stataic_p, f_is_stataic_p2, length, length_2, smc_decl_part]\
                        = self.oacc_smc_codegen_declaration(kernelId, kernelB, p, pivot2,\
                                                            v, up, dw, up2range, dw2range,\
                                                            ctadimx, ctadimy, t, 1)
                    decl += smc_decl_part
                    # print decl
                    if st=='READ_ONLY' or st=='READ_WRITE' or st=='FETCH_CHANNEL':
                        pre_region ='__syncthreads();\n'
                        pre_region+='{ // fetch begins\n'
                        # 1. specify the boundry 
                        [set_boundary_pointers, kernelB] = self.oacc_smc_codegen_set_boundary_pointers(\
                                        kernelId, kernelB, p, pivot2, v, up, dw,\
                                        up2range, dw2range, ctadimx, ctadimy, t,\
                                        isfusion, fusionIdx, fusionSMC,\
                                        f_is_stataic_p, f_is_stataic_p2, 1)
                        # 2. fetch the data in using parallel available threads of thread-block
                        [datafetch, kernelB] = self.oacc_smc_codegen_initial_fetch(\
                                        kernelId, kernelB, p, pivot2, v, up, dw,\
                                        up2range, dw2range, ctadimx, ctadimy, t,\
                                        dimlo, dimhi, dim2low, dim2high,\
                                        isfusion, fusionIdx, fusionSMC,\
                                        f_is_stataic_p, f_is_stataic_p2, 1)
                        post_region='#define '+v+'(index) __smc_select_'+str(a)+'_'+v+'(index, '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_endpointer+v+', '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_cuda+', '+p+', '+dw+', '+self.prefix_kernel_smc_startpointer+v+','+dimlo+','+dimhi+')\n'
                        code_to_inject = pre_region+set_boundary_pointers+datafetch+post_region+'\n'+fcall
                        kernelB = kernelB.replace(fcall, code_to_inject)



                    # [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kernelId)
                    # # print type(ctadimx), type(dw), type(up)
                    # length=ctadimx+'+'+dw+'+'+up
                    # #length=self.blockDim_cuda+'+'+dw+'+'+up
                    # # declare local memories
                    # decl+='\n/* declare the shared memory of '+v+' */\n'
                    # decl+='__shared__ '+t.replace('*','')+' '+self.prefix_kernel_smc_varpref+v+'['+length+'];\n'
                    # decl+='//__shared__ unsigned char '+self.prefix_kernel_smc_tagpref+v+'['+length+'];\n'
                    # if CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_COMMUN:  
                    #     decl+='__shared__ int '+self.prefix_kernel_smc_startpointer+v+';\n'
                    #     decl+='__shared__ int '+self.prefix_kernel_smc_endpointer+v+';\n'
                    # elif CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_PRIVATE:
                    #     decl+='int '+self.prefix_kernel_smc_startpointer+v+';\n'
                    #     decl+='int '+self.prefix_kernel_smc_endpointer+v+';\n'
                    # else:
                    #     print_error('cache: unknown pointer calculation method!', [])
                    # decl+=self.prefix_kernel_smc_endpointer+v+'=-1;\n'
                    # decl+=self.prefix_kernel_smc_startpointer+v+'=-1;\n'
                    # decl+='/*{\n'
                    # decl+='int iterator_of_smc=0;\n'
                    # decl+='for(iterator_of_smc=threadIdx.x; iterator_of_smc<('+length+'); iterator_of_smc+=blockDim.x){\n'
                    # decl+='//'+self.prefix_kernel_smc_varpref+v+'[iterator_of_smc]=0;\n'
                    # decl+=self.prefix_kernel_smc_tagpref+v+'[iterator_of_smc]=0;\n'
                    # decl+='}\n__syncthreads();\n'
                    # decl+='}*/\n'
                    # if st=='READ_ONLY' or st=='READ_WRITE' or st=='FETCH_CHANNEL':
                    #     # fetch data to local memory
                    #     datafetch ='{ // fetch begins\n'
                    #     datafetch +=' // FIXME: this region should be unmasked, having all threads of the thread-block active,\n'
                    #     datafetch +=' //        this is not the case always.\n'
                    #     if CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_COMMUN:  
                    #         datafetch +="""int __ipmacc_stride=__syncthreads_count(true);
                    #                        if(threadIdx.x==0){
                    #                            """+self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+""";
                    #                        }
                    #                        if(threadIdx.x==(__ipmacc_stride-1)){
                    #                            """+self.prefix_kernel_smc_endpointer+v+'='+p+'+'+dw+'+'+up+""";
                    #                        }
                    #                        __syncthreads();
                    #                     """
                    #     elif CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_PRIVATE:
                    #         datafetch+='int __ipmacc_stride=blockDim.x;\n'
                    #         datafetch+="bool lastcol= blockIdx.x==(gridDim.x-1);\n"
                    #         if (self.is_function_of_iterator_var(kernelId,kernelB,p)):
                    #             datafetch+=self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+'-threadIdx.x;\n'
                    #             datafetch+=self.prefix_kernel_smc_endpointer+v+'='+'blockDim.x+'+self.prefix_kernel_smc_startpointer+v+'+'+up+'+'+dw+'-1;\n'
                    #         else:
                    #             datafetch+=self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+';\n'
                    #             datafetch+=self.prefix_kernel_smc_endpointer+v+'='+self.prefix_kernel_smc_startpointer+v+'+'+up+'+'+dw+';\n'
                    #     else:
                    #         print_error('cache: unknown pointer calculation method!', [])
                    #     datafetch+='int __ipmacc_length='+self.prefix_kernel_smc_endpointer+v+'-'+self.prefix_kernel_smc_startpointer+v+'+1;\n'
                    #     if GENDEBUGCODE:
                    #         datafetch+='assert((__ipmacc_length)<=(256+'+dw+'+'+up+'));\n' #FIXME
                    #     datafetch+='int kk=0;\n'
                    #     if dw.strip()=='0' and up.strip()=='0':
                    #         datafetch+="kk=threadIdx.x;\n";
                    #     else:
                    #         datafetch+='for(int kk=threadIdx.x; kk<__ipmacc_length; kk+=__ipmacc_stride)\n'
                    #     datafetch+='{\n'
                    #     datafetch+='int idx='+self.prefix_kernel_smc_startpointer+v+'+kk;\n'
                    #     datafetch+='if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
                    #     datafetch+='{\n'
                    #     datafetch+=self.prefix_kernel_smc_varpref+v+'[kk]='+v+'[idx];\n'
                    #     datafetch+='//'+self.prefix_kernel_smc_tagpref+v+'[kk]=1;\n'
                    #     datafetch+='}\n'
                    #     datafetch+='}\n'
                    #     datafetch+='__syncthreads();\n'
                    #     datafetch+='} // end of fetch\n'
                    #     # pragma to replace global memory access with smc 
                    #     datafetch+='#define '+v+'(index) __smc_select_'+str(a)+'_'+v+'(index, '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_endpointer+v+', '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_cuda+', '+p+', '+dw+', '+self.prefix_kernel_smc_startpointer+v+','+dimlo+','+dimhi+')\n'
                    #     kernelB=kernelB.replace(fcall,datafetch+'\n'+fcall)
                    # construct the smc_select_ per array for READ
                    smc_select_calls+='__forceinline__ __device__ '+t.replace('*','')+' __smc_select_'+str(a)+'_'+v+'(int index, '+t+' g_array, '+t+' s_array, int startptr, int endptr, int diff){\n'
                    if div=='false':
                        smc_select_calls+='// the pragmas are well-set. do not check the boundaries.\n'
                        if GENDEBUGCODE:
                            smc_select_calls+='assert((index-startptr)>=0);\n' #FIXME
                            smc_select_calls+='assert((index-startptr)<260);\n' #FIXME
                            smc_select_calls+='assert(index>=lbnd);\n'
                            smc_select_calls+='assert(index>=down);\n'
                            smc_select_calls+='assert(index<ubnd);\n'
                            smc_select_calls+='assert(index<=up);\n'
                        smc_select_calls+='return s_array[index-startptr];\n'
                    else:
                        smc_select_calls+='// The tile is not well covered by the pivot, dw-range, and up-range\n'
                        smc_select_calls+='// dynamic runtime performs the check\n'
                        smc_select_calls+=t.replace('*','')+' ret = s_array[diff];\n'
                        smc_select_calls+='if(!(startptr<=index && index<=endptr)){\n'
                        smc_select_calls+=' ret = g_array[index];\n' #FIXME seriously
                        smc_select_calls+='}\n'
                        smc_select_calls+='return ret;\n'
                    smc_select_calls+='}\n'
                    # construct the smc_write_ per array for WRITE
                    smc_write_calls+='__device__ void __smc_write_'+str(a)+'_'+v+'(int index, int down, int up, '+t+' g_array, '+t+' s_array, int vector_size, int pivot, int before,'+t.replace('*','')+' value, int startptr){\n'
                    if div=='false':
                        smc_write_calls+='// the pragmas are well-set. do not check the boundaries.\n'
                        smc_write_calls+='s_array[index-startptr]=value;\n'
                    else:
                        smc_write_calls+='// The tile is not well covered by the pivot, dw-range, and up-range\n'
                        smc_write_calls+='// dynamic runtime performs the check\n'
                        smc_write_calls+='bool a=index>=down;\n'
                        smc_write_calls+='bool b=index<up;\n'
                        smc_write_calls+='bool d=a&b;\n'
                        smc_write_calls+='if(d){\n'
                        smc_write_calls+='s_array[index-startptr]=value;\n'
                        smc_write_calls+='}\n'
                        smc_write_calls+='g_array[index]=value;\n'
                    smc_write_calls+='}\n'
                    # replace array-ref [] with function call ()
                    fcallst=self.prefix_kernel_smc_fetch+str(a)+'();'
                    fcallen=self.prefix_kernel_smc_fetchend+str(a)+'();'
                    changeRangeIdx_start=kernelB.find(fcallst)
                    changeRangeIdx_end=kernelB.find(fcallen)
                    #print kernelB[changeRangeIdx_start:changeRangeIdx_end]
                    if (changeRangeIdx_start==-1 ) or (changeRangeIdx_end==-1) or (changeRangeIdx_start>changeRangeIdx_end):
                        print 'fatal error! could not determine the smc range for '+v
                        exit(-1)
                    # READ WRITE REPLACE ACCESSES
                    [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet] = self.smc_kernelBody_parse(kernelB, changeRangeIdx_start, changeRangeIdx_end, a, v, st, dim2high, p, dw, up)
                    for idx_num in range(len(readIdxStartEndPtrs)-1, -1, -1):
                        [idx_s, idx_e]=readIdxStartEndPtrs[idx_num]
                        if DEBUGSMCPRECALCINDEX:
                            print '> '+kernelB[idx_s:idx_e]
                        if div=='false':
                            kernelB=kernelB[:idx_s]+self.prefix_kernel_smc_varpref+v+'['+'__ipmacc_smc_index_'+v+'_'+str(readIdxList[idx_num])+'_dim1'+']'+' /* replacing '+kernelB[idx_s:idx_e]+'*/ '+kernelB[idx_e:]
                        else:
                            [tmp_idx1, tmp_idx2] = self.decompose1Dindexto2D(unifiedIdxSet[unifiedIdxList[idx_num]], '0', '', '1D')
                            tmp_diff1=tmp_idx1+'-'+self.prefix_kernel_smc_startpointer+v
                            access_tmp='__smc_select_'+str(a)+'_'+v+'('+tmp_idx1+', '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_endpointer+v+', '+tmp_diff1+')'
                            kernelB=kernelB[:idx_s]+access_tmp+'/* '+kernelB[idx_s:idx_e]+'*/ '+kernelB[idx_e:]

                    indexCalculationCode=self.smc_get_indexCalculation(readIdxSet, readIdxList, v, dim2high, writeIdxSet, writeIdxList, unifiedIdxSet, unifiedIdxList, '1D')
                    kernelB=kernelB.replace(fcall,indexCalculationCode+fcall)
                    changeRangeIdx_start=kernelB.find(fcallst)
                    changeRangeIdx_end=kernelB.find(fcallen)
                    [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet] = self.smc_kernelBody_parse(kernelB, changeRangeIdx_start, changeRangeIdx_end, a, v, st, dim2high, p, dw, up)
                    # list all read accesses
                    # unpack and replace write-accesses
                    for wi in range(len(writeIdxStartEndPtrs)-1,-1,-1):
                        [v, a, p, dw, up, wst, wen, asgidx]=writeIdxStartEndPtrs[wi]
                        writeIdx_loc=']'.join('['.join(kernelB[wst:asgidx].split('[')[1:]).split(']')[:-1])
                        writeIdx_val=kernelB[asgidx+1:wen]
                        writeIdx_replacer ='__syncthreads();\n'
                        writeIdx_replacer+=self.prefix_kernel_smc_varpref+v+'['+'__ipmacc_smc_index_'+v+'_'+str(writeIdxList[wi])+'_dim1'+']='+writeIdx_val[:-1]+';\n'
                        writeIdx_replacer+='__syncthreads();\n'
                        kernelB=kernelB[0:wst]+writeIdx_replacer+kernelB[wen+1:]
                    # generate writeback code
                    if st=='READ_WRITE' or st=='WRITE_ONLY':
                        # fetch data to local memory
                        writeback ='{ // writeback begins\nint kk;\n'
                        writeback+='__syncthreads();\n'
                        if w_dw=='':
                            wlength=length
                        else:
                            wlength=self.blockDim_cuda+'+'+w_dw+'+'+w_up
                        writeback+='int rw_offset = '+dw+'-'+w_dw+';\n'
                        writeback+='int  __ipmacc_stride=__syncthreads_count(1);\n'
                        writeback+='for(int kk=threadIdx.x; kk<('+wlength+'); kk+=__ipmacc_stride)\n'
                        writeback+='{\n'
                        writeback+='int idx='+self.prefix_kernel_smc_startpointer+v+'+kk+rw_offset;\n'
                        writeback+='if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
                        writeback+='{\n'
                        writeback+=v+'[idx]='+self.prefix_kernel_smc_varpref+v+'[kk+rw_offset];\n'
                        writeback+='}\n'
                        writeback+='}\n'
                        writeback+='__syncthreads();\n'
                        writeback+='} // end of writeback\n' 
                        kernelB=kernelB.replace(fcallen,writeback+'\n'+fcallen)
                    # undef function call ()
                    if st=='READ_ONLY' or st=='READ_WRITE' or st=='FETCH_CHANNEL':
                        kernelB=kernelB.replace(fcallen,'#undef '+v+'\n'+fcallen)
                    pfreelist.append(a)
                else:
                    # for 2D SMC
                    [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kernelId)
                    if nctadim<=1: #not GENMULTIDIMTB:
                        print 'Error! multi-dimensional SMC works with multi-dimensional grid. Enable GENMULTIDIMTB in codegen.py'
                        exit(-1)
                    [f_is_stataic_p, f_is_stataic_p2, length, length_2, smc_decl_part]\
                        = self.oacc_smc_codegen_declaration(kernelId, kernelB, p, pivot2,\
                                                            v, up, dw, up2range, dw2range,\
                                                            ctadimx, ctadimy, t, 2)
                    decl += smc_decl_part

                    if st=='READ_ONLY' or st=='READ_WRITE' or st=='FETCH_CHANNEL':
                        # fetch data to local memory
                        pre_region ='__syncthreads();\n'
                        pre_region+='{ // fetch begins\n'
                        # 1. specify the boundry 
                        [set_boundary_pointers, kernelB] = self.oacc_smc_codegen_set_boundary_pointers(\
                                        kernelId, kernelB, p, pivot2, v, up, dw,\
                                        up2range, dw2range, ctadimx, ctadimy, t,\
                                        isfusion, fusionIdx, fusionSMC,\
                                        f_is_stataic_p, f_is_stataic_p2, 2)
                        # 2. fetch the data in using parallel available threads of thread-block
                        [datafetch, kernelB] = self.oacc_smc_codegen_initial_fetch(\
                                        kernelId, kernelB, p, pivot2, v, up, dw,\
                                        up2range, dw2range, ctadimx, ctadimy, t,\
                                        dimlo, dimhi, dim2low, dim2high,\
                                        isfusion, fusionIdx, fusionSMC,\
                                        f_is_stataic_p, f_is_stataic_p2, 2)
                        post_region='} // end of fetch\n'
                        code_to_inject = pre_region+set_boundary_pointers+datafetch+post_region+'\n'+fcall
                        kernelB = kernelB.replace(fcall, code_to_inject)
                    # inject cache read/write calls
                    [smc_select_call, smc_write_call] = self.oacc_smc_codegen_readwrite_calls(t, a, v, length, length_2, div)
                    smc_select_calls += smc_select_call
                    smc_write_calls += smc_write_call

                    # replace array-ref [] with function call ()
                    [fcallen, kernelB] = self.oacc_smc_codegen_cache_region_replace_accesses(a, v, t,\
                                    p, dw, up,\
                                    pivot2, dw2range, up2range,\
                                    dim2high, div, fcall,\
                                    kernelB, st)

                    # generate writeback code
                    if st=='READ_WRITE' or st=='WRITE_ONLY':
                        kernelB = self.oacc_smc_codegen_writeback(length, length_2, w_dw, w_up,\
                                        w_dw2range, w_up2range, v, dimlo, dimhi, dim2low, dim2high, fcallen)

                    # undef function call ()
                    if st=='READ_ONLY' or st=='READ_WRITE'  or st=='FETCH_CHANNEL':
                        kernelB=kernelB.replace(fcallen,'#undef '+v+'\n'+fcallen)
                    # Fusion Control
                    fusionSMC.append([p,dw,up,pivot2,dw2range,up2range,v])
                    # 
                    pfreelist.append(a)
            for ids in pfreelist:
                fcallst=self.prefix_kernel_smc_fetch+str(ids)+'();'
                fcallen=self.prefix_kernel_smc_fetchend+str(ids)+'();'
                kernelB=kernelB.replace(fcallst,'')
                kernelB=kernelB.replace(fcallen,'')

        compKernelB=kernelB
        if len(compInfo)>0:
            for compVarObj in compInfo:
                for arrayRef in re.finditer('\\b'+compVarObj.varName+'[\\ \\t\\n\\r]*\[',compKernelB):
                    arrayRef_it=arrayRef.start(0)
                    arrayRef_pcnt=0
                    done=False
                    openIndex=0
                    closeIndex=0
                    while not done:
                        if compKernelB[arrayRef_it]=='[':
                            if arrayRef_pcnt==0:
                                #tempCode[arrayRef_it]='('
                                openIndex=arrayRef_it
                                #compKernelB=compKernelB[:arrayRef_it]+'('+compKernelB[arrayRef_it+1:]
                            arrayRef_pcnt+=1
                        elif compKernelB[arrayRef_it]==']':
                            arrayRef_pcnt-=1
                            if arrayRef_pcnt==0:
                                #tempCode[arrayRef_it]=')'
                                closeIndex=arrayRef_it
                                #compKernelB=compKernelB[:arrayRef_it]+')'+compKernelB[arrayRef_it+1:]
                                done=True
                        if done==True:
                            while True:
                                if compKernelB[arrayRef_it]=='=':
                                    compKernelB=compKernelB[:arrayRef_it+1]+" compress_"+compVarObj.type+'('+compKernelB[arrayRef_it+1:]
                                    compKernelB=compKernelB[:compKernelB.find(';',arrayRef_it)]+','+'__compress_constant_main_'+str(compVarObj.varName)+')'+compKernelB[compKernelB.find(';',arrayRef_it):]
                                    break;
                                elif compKernelB[arrayRef_it]==';':
                                    compKernelB=compKernelB[:openIndex]+'('+compKernelB[openIndex+1:]
                                    compKernelB=compKernelB[:closeIndex]+')'+compKernelB[closeIndex+1:]
                                    break;
                                arrayRef_it+=1
                        arrayRef_it+=1
                proto="__constant__ "+compVarObj.type+" __compress_constant_main_"+compVarObj.varName+"[10];\n"+proto
        middleCode=code
        code=simpleCodeInit
        code+=middleCode
        code='\n'.join([smc_select_calls,smc_write_calls])+code
        code+=decl
        # update the boolean guard for every writes to scalar variables
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                scalvname = vname.replace('__ipmacc_scalar','')
                kernelB = self.guard_write_to_scalar_variable(kernelB, scalvname)
        code+=kernelB
        code+='//append writeback of scalar variables\n'
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                code+='if('+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard'+'){\n'
                code+=vname+'[0]='+vname.replace('__ipmacc_scalar','')+';\n'
                code+='}\n'
        code=code+'}\n'
        code=self.fix_call_args(code) #CUDA
        compCode=''
        if len(self.oacc_kernelsComp[kernelId])!=0:
            compCode=compCodeInit
            compCode+=middleCode
            compCode='\n'.join([smc_select_calls,smc_write_calls])+compCode
            compCode+=decl
            compCode+=compKernelB
            compCode=compCode+'}\n'
            for compVarObj in self.oacc_kernelsComp[kernelId]:
                compCode+='#undef '+str(compVarObj.varName) + '\n'
        #for [fname, prototype, declbody] in self.active_calls_decl:
        #    code=re.sub('\\b'+fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+fname+'(', code)
        #for [fname, prototype, declbody] in self.active_calls_decl:
        #    compCode=re.sub('\\b'+fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+fname+'_compression(', compCode)
        #    m=re.search(fname+'_compression\s*\((.*?)\)',compCode,re.S)
        #    if m:
        #        argList = m.group(1).split(',')
        #        for compVarObj in self.oacc_kernelsComp[kernelId]:
        #            for arg in argList:
        #                if arg.strip()==str(compVarObj.varName):
        #                    argList.append('__compress_constant_'+str(compVarObj.varName))
        #        compCode=compCode.replace(m.group(0),fname+'_compression('+','.join(argList)+')')
        return [proto, code+compCode]


    def decompose1Dindexto2D(self, index,dim1,dim2,dimtype):
        if dimtype=="1D":
            return [index, "0"]
        elif dimtype=="2D":
            try:
                [p1,p2]=index.split('+')
                if p1.find('*')!=-1:
                    C=p1
                    B=p2
                elif p2.find('*')!=-1:
                    C=p2
                    B=p1
    
                [p3,p4]=C.split('*')
                if p3==dim2:
                    A=p4
                elif p4==dim2:
                    A=p3
                #print '['+A+']['+B+']'
                return [A,B]
            except:
                print 'Unable to parse index expression! expected to parse index in the following form:'
                print ' A*'+dim2+'+B where A and B are variables and dim2 is the number of elements in the columns.'
                print ' index term> '+index
                exit(-1)
        else:
            print 'unimplemented dimension type> '+dimtype
            exit(-1)

    def smc_get_indexCalculation(self, readIdxSet, readIdxList, v, dim2high, writeIdxSet, writeIdxList, unifiedIdxSet, unifiedIdxList, dimtype):
        indexCalculationCode='// '+str(len(unifiedIdxSet))+' unique indexes\n'
        for rd in range(0,len(unifiedIdxSet),1):
            indexCalculationCode+='// ['+str(rd)+'] '+unifiedIdxSet[rd]+'\n'
            [A,B] = self.decompose1Dindexto2D(unifiedIdxSet[rd], '0', dim2high, dimtype)
            indexCalculationCode+='\t#define __ipmacc_smc_index_'+v+'_'+str(rd)+'_dim1 '+A+'-'+self.prefix_kernel_smc_startpointer+v+'\n'
            if dimtype!='1D':
                indexCalculationCode+='\t#define __ipmacc_smc_index_'+v+'_'+str(rd)+'_dim2 '+B+'-'+self.prefix_kernel_smc_startpointer+v+'_2d\n'
        if DEBUGSMCPRECALCINDEX:
            print indexCalculationCode
        return indexCalculationCode

    def guard_write_to_scalar_variable(self, kernelB, v):
        # updates the guard for every write to the scalar variable
        # kernelB: body of the code to look into
        # v: variable to look for writes to
        # note: use smc_kernelBody_parse to find writes to an array
        changeRangeIdx_start=0
        changeRangeIdx_end=len(kernelB)-1
        writeIdxStartPtrs=[]
        newKernelB=''
        for arrayRef in re.finditer('\\b'+v+'[\\ \\t\\n\\r]*',kernelB[changeRangeIdx_start:changeRangeIdx_end]):
            arrayRef_it=changeRangeIdx_start+arrayRef.start(0)
            iswrite=False
            assignmentIdx=-1
            assignmentOpr='='
            # find if this is an assignment to v 
            while True:
                if kernelB[arrayRef_it]==';':
                    break
                elif kernelB[arrayRef_it]=='=' and kernelB[arrayRef_it+1]!='=' and (kernelB[arrayRef_it-1]==' ' or kernelB[arrayRef_it-1]=='\t' or kernelB[arrayRef_it-1]=='\n' or kernelB[arrayRef_it-1]=='+' or kernelB[arrayRef_it-1]=='|' or kernelB[arrayRef_it-1]=='&' or kernelB[arrayRef_it-1]=='-' or kernelB[arrayRef_it-1]=='\\' or kernelB[arrayRef_it-1]=='*' or kernelB[arrayRef_it-1]=='^' or kernelB[arrayRef_it-1]=='%' or kernelB[arrayRef_it-1].isalpha() or kernelB[arrayRef_it-1].isdigit()):
                    iswrite=True
                    assignmentIdx=arrayRef_it
                    if not (kernelB[arrayRef_it-1].isalpha() or kernelB[arrayRef_it-1].isdigit()):
                        assignmentOpr=(kernelB[arrayRef_it-1]+'=').strip()
                arrayRef_it+=1
            if iswrite:
                wrtIdx_start = changeRangeIdx_start+arrayRef.start(0)
                if DEBUGSCALRVAR:
                    print 'write statement found at ['+str(wrtIdx_start)+'] ...'+kernelB[wrtIdx_start-4:wrtIdx_start+4]+'...'
                writeIdxStartPtrs.append(wrtIdx_start)
            else:
                wrtIdx_start = changeRangeIdx_start+arrayRef.start(0)
                if DEBUGSCALRVAR:
                    print 'no write statement found at ['+str(wrtIdx_start)+'] ...'+kernelB[wrtIdx_start-4:wrtIdx_start+4]+'...'
        # UPDATE KERNEL
        newKernelB=kernelB
        for wi in range(len(writeIdxStartPtrs)-1,-1,-1):
            wst=writeIdxStartPtrs[wi]
            newKernelB=newKernelB[0:wst-1]+'\n'+v+'__ipmacc_guard = true;\n'+newKernelB[wst:]
        return newKernelB

    def util_is_written_to(self, code, vname, offset):
        try:
            #print 'looking for', vname, 'in', code.replace('\n',' ').strip()[:40]
            #skip to the end of variable
            arrayRef_it=offset
            arrayRef_pcnt=0
            done=False
            while not done:
                if code[arrayRef_it]=='[':
                    arrayRef_pcnt+=1
                elif code[arrayRef_it]==']':
                    arrayRef_pcnt-=1
                    if arrayRef_pcnt==0:
                        done=True
                arrayRef_it+=1
            # check whether it is a write access
            iswrite=False
            assignmentIdx=-1
            assignmentOpr='='
            while True:
                if code[arrayRef_it]==';':
                    break
                elif code[arrayRef_it]=='=' and code[arrayRef_it+1]!='=' and (code[arrayRef_it-1]==' ' or code[arrayRef_it-1]=='\t' or code[arrayRef_it-1]=='\n' or code[arrayRef_it-1]=='+' or code[arrayRef_it-1]=='|' or code[arrayRef_it-1]=='&' or code[arrayRef_it-1]=='-' or code[arrayRef_it-1]=='\\' or code[arrayRef_it-1]=='*' or code[arrayRef_it-1]=='^' or code[arrayRef_it-1]=='%' or code[arrayRef_it-1].isalpha() or code[arrayRef_it-1].isdigit()):
                    iswrite=True
                    assignmentIdx=arrayRef_it
                    if not (code[arrayRef_it-1].isalpha() or code[arrayRef_it-1].isdigit()):
                        assignmentOpr=(code[arrayRef_it-1]+'=').strip()
                arrayRef_it+=1
            # keep the track of write accesses 
            if iswrite:
                writeIdx_str=offset
                writeIdx_end=arrayRef_it+1
                writeIdx_loc=']'.join('['.join(code[writeIdx_str:assignmentIdx].split('[')[1:]).split(']')[:-1]).replace(' ','')
                writeIdx_val=code[assignmentIdx+1:writeIdx_end]
            else:
                writeIdx_str = -1
                writeIdx_end = -1
                writeIdx_loc = ''
                writeIdx_val = ''
            return [iswrite, assignmentIdx, assignmentOpr, writeIdx_str, writeIdx_end, writeIdx_loc, writeIdx_val]
        except Exception as e:
            print e
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print exc_tb
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print exc_type, fname, exc_tb.tb_lineno
            exit(-1)

    def find_kernel_writes(self, code, kid):
        try:
            [arraccs,indecis,dependt] = srcml_get_arrayaccesses(srcml_code2xml(code), [])
            # get location of every arraccs[] in code; 
            # first find them in the code
            # second append them to the list
            remap = {}
            # print code
            # print 'set:', list(set(arraccs))
            for v  in list(set(arraccs)):
                if not( v in remap):
                    remap[v] = []
                for arrayRef in re.finditer('\\b'+v.strip()+'[\\ \\t\\n\\r]*\[',code):
                    arrayRef_it=arrayRef.start(0)
                    # print arrayRef_it, v
                    remap[v].append(arrayRef_it)
            arraccs_loc = []
            # print 'list:', arraccs
            for v in arraccs:
                if len(remap[v])>0:
                    arrayRef_it = remap[v].pop(0)
                    # print 'pop:', arrayRef_it, v
                else:
                    print_error('unable to find array location', ['variable: '+v])
                arraccs_loc.append(arrayRef_it)
            if len(arraccs)!=len(arraccs_loc):
                print 'internal error: failed to locate array access'
                print 'procedure: find_kernel_writes'
                print 'arrays:', len(arraccs)
                print 'locations:', len(arraccs_loc)
                print 'aborting()'
                exit(-1)

            # having the locations of array accesses in the code,
            # isolates reads and writes
            kernelwrites = []
            kernelreads  = []
            for idx in range(0,len(arraccs)):
                offset = arraccs_loc[idx]
                # skip local array read/writes
                if not arraccs[idx].strip() in self.oacc_kernelsVarNams[kid]:
                    continue
                # proceed with global read/writes
                [iswrite, assignmentIdx, assignmentOpr, writeIdx_str, writeIdx_end, writeIdx_loc, writeIdx_val] = self.util_is_written_to(code[offset:], arraccs[idx], 0)
                if iswrite:
                    kernelwrites.append([arraccs[idx], indecis[idx], dependt[idx], arraccs_loc[idx], offset+assignmentIdx, assignmentOpr, offset+writeIdx_str, offset+writeIdx_end, writeIdx_loc])
                else:
                    kernelreads.append([arraccs[idx], indecis[idx], dependt[idx], arraccs_loc[idx]])
            return [kernelwrites, kernelreads]
        except Exception as e:
            print e
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print exc_tb
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print exc_type, fname, exc_tb.tb_lineno
            exit(-1)

    def smc_kernelBody_parse(self, kernelB, changeRangeIdx_start, changeRangeIdx_end, arg_smc_uid, arg_smc_subarray_name, arg_smc_type, arg_smc_subarray_d2_size, arg_smc_range_p, arg_smc_range_dw, arg_smc_range_up):
        a  = arg_smc_uid
        v  = arg_smc_subarray_name
        st = arg_smc_type
        dim2high = arg_smc_subarray_d2_size
        p  = arg_smc_range_p
        dw = arg_smc_range_dw
        up = arg_smc_range_up
        writeIdxList=[]
        writeIdxSet=[]
        writeIdxStartEndPtrs=[]
        readIdxList=[]
        readIdxSet=[]
        readIdxStartEndPtrs=[]
        unifiedIdxSet=[]
        unifiedIdxList=[]
        for arrayRef in re.finditer('\\b'+v+'[\\ \\t\\n\\r]*\[',kernelB[changeRangeIdx_start:changeRangeIdx_end]):
            #skip to the end of variable
            [iswrite, assignmentIdx, assignmentOpr, writeIdx_str, writeIdx_end, writeIdx_loc, writeIdx_val] = self.util_is_written_to(kernelB, v, changeRangeIdx_start+arrayRef.start(0))
            # arrayRef_it=changeRangeIdx_start+arrayRef.start(0)
            # arrayRef_pcnt=0
            # done=False
            # while not done:
            #     if kernelB[arrayRef_it]=='[':
            #         #if arrayRef_pcnt==0:
            #             #kernelB[arrayRef_it]='('
            #             #kernelB=kernelB[:arrayRef_it]+'('+kernelB[arrayRef_it+1:]
            #         arrayRef_pcnt+=1
            #     elif kernelB[arrayRef_it]==']':
            #         arrayRef_pcnt-=1
            #         if arrayRef_pcnt==0:
            #             #kernelB[arrayRef_it]=')'
            #             #kernelB=kernelB[:arrayRef_it]+')'+kernelB[arrayRef_it+1:]
            #             done=True
            #     arrayRef_it+=1
            # # check whether it is a write access
            # iswrite=False
            # assignmentIdx=-1
            # assignmentOpr='='
            # while True:
            #     if kernelB[arrayRef_it]==';':
            #         break
            #     elif kernelB[arrayRef_it]=='=' and kernelB[arrayRef_it+1]!='=' and (kernelB[arrayRef_it-1]==' ' or kernelB[arrayRef_it-1]=='\t' or kernelB[arrayRef_it-1]=='\n' or kernelB[arrayRef_it-1]=='+' or kernelB[arrayRef_it-1]=='|' or kernelB[arrayRef_it-1]=='&' or kernelB[arrayRef_it-1]=='-' or kernelB[arrayRef_it-1]=='\\' or kernelB[arrayRef_it-1]=='*' or kernelB[arrayRef_it-1]=='^' or kernelB[arrayRef_it-1]=='%' or kernelB[arrayRef_it-1].isalpha() or kernelB[arrayRef_it-1].isdigit()):
            #         iswrite=True
            #         assignmentIdx=arrayRef_it
            #         if not (kernelB[arrayRef_it-1].isalpha() or kernelB[arrayRef_it-1].isdigit()):
            #             assignmentOpr=(kernelB[arrayRef_it-1]+'=').strip()
            #     arrayRef_it+=1
            # # keep the track of write accesses 
            if iswrite and (st=='WRITE_ONLY' or st=='READ_WRITE' or  st=='FETCH_CHANNEL'):
                #writeIdx_str=changeRangeIdx_start+arrayRef.start(0)
                #writeIdx_end=arrayRef_it+1
                #writeIdx_loc=']'.join('['.join(kernelB[writeIdx_str:assignmentIdx].split('[')[1:]).split(']')[:-1]).replace(' ','')
                #writeIdx_val=kernelB[assignmentIdx+1:writeIdx_end]
                #writeIdx_replacer='__smc_write_'+str(a)+'_'+v+'('+v+','+self.prefix_kernel_smc_varpref+v+','+writeIdx_loc+','+writeIdx_val[:-1]+');'
                #writeIdx_replacer='__syncthreads();\n__smc_write_'+str(a)+'_'+v+'('+writeIdx_loc+', ('+self.prefix_kernel_smc_startpointer+v+'), ((blockIdx.x+1)*'+self.blockDim_cuda+')+('+up+'), '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_cuda+', '+p+', '+dw+','+writeIdx_val[:-1]+', '+self.prefix_kernel_smc_startpointer+v+');\n'
                #writeIdx_replacer='//__syncthreads();\n//__smc_write_'+str(a)+'_'+v+'('+writeIdx_loc+', (blockIdx.x*'+self.blockDim_cuda+')-('+dw+'), ((blockIdx.x+1)*'+self.blockDim_cuda+')+('+up+'), '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_cuda+', '+p+', '+dw+','+writeIdx_val[:-1]+', '+self.prefix_kernel_smc_startpointer+v+');\n'
                writeIdx_replacer='__syncthreads();\n__smc_write_'+str(a)+'_'+v+'('+writeIdx_loc+', '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_startpointer+v+'_2d, '+dim2high+', '+writeIdx_val[:-1]+')\n'
                writeIdx_replacer+='__syncthreads();\n'
                writeIdxStartEndPtrs.append([v, a, p, dw, up, writeIdx_str, writeIdx_end, assignmentIdx])
                try:
                    newAccess=unifiedIdxSet.index(writeIdx_loc)
                except:
                    newAccess=-1
                if newAccess==-1:
                    writeIdxList.append(len(unifiedIdxSet))
                    writeIdxSet.append(writeIdx_loc)
                    unifiedIdxList.append(len(unifiedIdxSet))
                    unifiedIdxSet.append(writeIdx_loc)
                else:
                    writeIdxList.append(newAccess)
                    unifiedIdxList.append(newAccess)
            if (st=='READ_ONLY' or st=='READ_WRITE'  or st=='FETCH_CHANNEL') and not iswrite:
                #replace [ and ] with ( and )
                arrayRef_it=changeRangeIdx_start+arrayRef.start(0)
                arrayRef_pcnt=0
                done=False
                index_ptr_st=-1
                index_ptr_en=-1
                wholeread_ptr_st=arrayRef_it
                wholeread_ptr_en=-1
                while not done:
                    if kernelB[arrayRef_it]=='[':
                        if arrayRef_pcnt==0:
                            #kernelB[arrayRef_it]='('
                            kernelB=kernelB[:arrayRef_it]+'('+kernelB[arrayRef_it+1:]
                            index_ptr_st=arrayRef_it+1
                        arrayRef_pcnt+=1
                    elif kernelB[arrayRef_it]==']':
                        arrayRef_pcnt-=1
                        if arrayRef_pcnt==0:
                            #kernelB[arrayRef_it]=')'
                            kernelB=kernelB[:arrayRef_it]+')'+kernelB[arrayRef_it+1:]
                            index_ptr_en=arrayRef_it
                            wholeread_ptr_en=arrayRef_it+1
                            done=True
                    arrayRef_it+=1
                readIdxStartEndPtrs.append([wholeread_ptr_st, wholeread_ptr_en])
                try:
                    newAccess=unifiedIdxSet.index(kernelB[index_ptr_st:index_ptr_en].replace(' ',''))
                except:
                    newAccess=-1
                if newAccess==-1:
                    readIdxList.append(len(unifiedIdxSet))
                    readIdxSet.append(kernelB[index_ptr_st:index_ptr_en].replace(' ',''))
                    unifiedIdxList.append(len(unifiedIdxSet))
                    unifiedIdxSet.append(kernelB[index_ptr_st:index_ptr_en].replace(' ',''))
                else:
                    readIdxList.append(newAccess)
                    unifiedIdxList.append(newAccess)
        if DEBUGCACHE:
            print [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet]
        return [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet]
    def memAlloc_cuda(self, var, size):
        codeM='cudaMalloc((void**)&'+var+','+size+');\n'
        return codeM
    def memCpy_cuda(self, des, src, size, type):
        codeC='cudaMemcpy('+des+','+src+','+size+','+('cudaMemcpyHostToDevice' if type=='in' else 'cudaMemcpyDeviceToHost')+');\n'
        return codeC
    def devPtrDeclare_cuda(self, type, name, sccopy):
        return type+('* ' if sccopy else ' ')+name+';\n'
    def getTypeFwrDecl_cuda(self):
        type_decls=''
        for [nm, fwdcl, fudcl, oclfudcl, oclparent] in self.active_types_decl:
            type_decls+=fwdcl+'\n'
        return type_decls
    def atomic_cuda(self, atomicBody, atomicClause, kernelId, lockindex):
        lockvariable=self.prefix_kernel_atomicLocks+'['+str(lockindex)+']'
        if atomicClause=='capture':
            code="""{
                      bool __ipmacc_leaveLoop = false;
                      while (!__ipmacc_leaveLoop) {
                        if (atomicExch(&("""+lockvariable+"""), 1u) == 0u) {
                          //critical section\n"""+atomicBody+"""\n
                          __ipmacc_leaveLoop = true;
                          atomicExch(&("""+lockvariable+"""),0u);
                        }
                      }
                    } 
            """
            return code
        else:
            print 'unimplemented atomic clause: '+atomicClause
            exit(-1)

    def cuda_sort_get_func(self):
        code=''
        calls=[]
        for tp in self.oacc_algoSort_Types2Overload:
            # print 'depreciated!'
            # print 'function should be updated to return a tuple like:'
            # print '[fname, prototype, declbody, rettype, qualifiers, params]'
            # print 'check srcML/wrapper/wrapper.py:getVarDetails() for latest'
            # print 'aborting()'
            # exit(-1)
            allfunctions = ''

            #fname = 'compare1_'+tp
            #prototype = 'uint '+fname+'(const '+tp+' &left, const '+tp+' &right)'
            #qualifiers = []
            #rettype = 'uint'
            #params = [ ['const '+tp+'&', 'const '+tp+'&'], ['left', 'right'], []] 
            declbody ="""
                //uint compare1_"""+tp+"""("""+tp+""" &left, """+tp+""" &right)
                uint compare1_"""+tp+"""(const """+tp+""" &left, const """+tp+""" &right)
                {
                    if(left>right){
                        return true;
                    }else{
                        return false;
                    }
                }
                """
            allfunctions += declbody
            #calls.append([fname, prototype, declbody, rettype, qualifiers, params])
            #calls.append(fcns[0])
            #print fcns
            #exit(-1)

            #fname = 'compare2_'+tp
            #prototype = 'uint '+fname+'(const '+tp+' &left, const '+tp+' &right)'
            #qualifiers = []
            #rettype = 'uint'
            #params = [ ['const '+tp+'&', 'const '+tp+'&'], ['left', 'right'], []] 
            declbody ="""
                //uint compare2_"""+tp+"""("""+tp+""" &left, """+tp+""" &right)
                uint compare2_"""+tp+"""(const """+tp+""" &left, const """+tp+""" &right)
                {
                    if(left>=right){
                        return true;
                    }else{
                        return false;
                    }
                }
                """
            allfunctions += declbody
            [typs, fcns] = srcml_get_fwdecls(allfunctions, [], [('compare1_'+tp).strip(), ('compare2_'+tp).strip()], [], [], 'CUDA')
            calls+= fcns
            #calls.append([fname, prototype, declbody, rettype, qualifiers, params])
        #exit(-1)
        return calls

    def algo_get_preferred_width(self, kernel_id):
        for [kid, length] in self.algorithm_execution_width:
            if kid==kernel_id:
                return '((int)pow(2, ceil(log('+length+')/log(2))))'
        print 'fatal error: couldn\'t determine thread block size.'
        print self.algorithm_execution_width
        exit(-1)

    def algo_update_preferred_width(self, kernel_id, clause):
        size_list = []
        for [i0, i3] in clauseDecomposer_break(clause):
            if DEBUGLD:
                print 'clause entry> '+'<>'.join([i0,i3]).strip()
            if i0.strip()=='sort':
                code=''
                code+="""// """+i3+"""\n"""
                for variable in i3.split(','): # FIXME: this stuck on complex range specifiers, like (suba[0:foo(1,2,3)],subb[0:foo(3,4,5)])
                    vname  = variable.split('[')[0]
                    config = variable.split('[')[1].split(']')[0]
                    range_low = config.split(':')[0]
                    range_hig = config.split(':')[1]
                    self.algorithm_execution_width.append([kernel_id, '('+range_hig+'-'+range_low+')'])
            elif i0.strip()=='find':
                code=''
                code+="""// """+i3+"""\n"""
                findargs = i3.split(',')  # FIXME: this stuck on complex range specifiers, like (suba[0:foo(1,2,3)],subb[0:foo(3,4,5)])
                variable = findargs[0]
                vname  = variable.split('[')[0]
                config = variable.split('[')[1].split(']')[0]
                range_low = config.split(':')[0]
                range_hig = config.split(':')[1]
                self.algorithm_execution_width.append([kernel_id, '('+range_hig+'-'+range_low+')'])
            else:
                print 'unknown clause for algorithm directive: ', i0.strip()
                exit(-1)

    def algo_cuda(self, algoBody, algoClause, kernelId, revdepnest):
        for [i0, i3] in clauseDecomposer_break(algoClause):
            if DEBUGLD:
                print 'clause entry> '+'<>'.join([i0,i3]).strip()
            if i0.strip()=='sort':
                code=''
                code+="""// """+i3+"""\n"""
                for variable in i3.split(','): # FIXME: this stuck on complex range specifiers, like (suba[0:foo(1,2,3)],subb[0:foo(3,4,5)])
                    vname  = variable.split('[')[0]
                    config = variable.split('[')[1].split(']')[0]
                    range_low = config.split(':')[0]
                    range_hig = config.split(':')[1]
                    try:
                        varNameList=self.oacc_kernelsLocalVarNams[kernelId]+self.oacc_kernelsVarNams[kernelId]
                        varTypeList=self.oacc_kernelsLocalVarTyps[kernelId]+self.oacc_kernelsVarTyps[kernelId]
                        vtype = varTypeList[varNameList.index(vname)]
                    except:
                        print 'error: unable to specify the type of variable in algorithm directive: '+vname
                        print 'aborting()'
                        exit(-1)
                    vtype_ispointer = vtype.count('*')
                    if vtype_ispointer!=1:
                        print 'error: only single dimensional sort is supported!'
                        print 'aborting()'
                        exit(-1)
                    vtype_noptr = vtype.replace('*','')
                    self.oacc_algoSort_Types2Overload.append(vtype_noptr)
                    code+="""// """+vname+"""\n"""
                    code+="""// """+vtype+"""\n"""
                    code+="""// """+config+"""\n"""
                    code+="""// """+range_low+"""\n"""
                    code+="""// """+range_hig+"""\n"""
                    code+="""// """+vtype_noptr+"""\n"""
                    if True:
                        # remap the variable to __shared__ scope
                        #bdx = self.oacc_kernelsConfig[kernelId]['blockDimx']
                        #bdy = self.oacc_kernelsConfig[kernelId]['blockDimy']
                        #bdz = self.oacc_kernelsConfig[kernelId]['blockDimz']
                        [nctadim, bdx, bdy, bdz]=self.oacc_kernelsConfig_getDecl(kernelId)
                        try:
                            bdx_i = int(bdx)
                            bdy_i = int(bdy)
                            bdz_i = int(bdz)
                        except:
                            print 'warning: cannot specify the value of vector clause statically, nvcc may fail to compile the code.'
                        if bdy=='1' and bdz=='1':
                            offset = '0'
                        else:
                            offset = '((blockDim.y*threadIdx.z+threadIdx.y)*('+range_hig+'-'+range_low+'))'
                        #_sort_global_size = '('+bdy+')*('+bdz+')*('+range_hig+'-'+range_low+')'
                        _sort_global_size = 'blockDim.x*blockDim.y*blockDim.z*2' # total shared memory allocated per thread block
                        _sort_global_size_in_bytes = '('+_sort_global_size+')*sizeof('+vtype_noptr+')' # total shared memory allocated per thread block
                        _sort_local_size  = 'blockDim.x*2' # size of shared memory independently processed
                        self.cuda_shared_memory_dynamic_alloc.append(_sort_global_size_in_bytes)
                        _sort_local_offset = '(blockDim.y*threadIdx.z+threadIdx.y)*('+_sort_local_size+')'
                        decl ='extern __shared__ '+vtype_noptr+' __ptr_dynamic_shared_allocation[];\n' #FIXME: SHOULD BE MOVED earlier in the kernel
                        #decl+=vtype_noptr+' *'+vname+' = ('+vtype_noptr+'*)&__ptr_dynamic_shared_allocation['+_sort_local_offset+'];\n'
                        decl+=vtype_noptr+' *'+vname+'_sort_local = ('+vtype_noptr+'*)&__ptr_dynamic_shared_allocation['+_sort_local_offset+'];\n'
                        decl+='// initialize the '+vname+'_sort_local array'
                        _init_value='1<<30'
                        decl+="""
                              {
                                 """+vname+"""_sort_local[threadIdx.x] = """+_init_value+""";
                                 """+vname+"""_sort_local[threadIdx.x+blockDim.x] = """+_init_value+""";
                                 //"""+vname+"""[threadIdx.x] = """+_init_value+""";
                                 //"""+vname+"""[threadIdx.x+blockDim.x] = """+_init_value+""";
                                 //for(unsigned int __ipmacc_tmp_i=0; __ipmacc_tmp_i<("""+_sort_local_size+"""); ++__ipmacc_tmp_i)
                                 //{
                                 //    """+vname+"""_sort_local[__ipmacc_tmp_i] = 1<<30;
                                 //}
                              }
                              """
                        code+="""// fetch
                             {
                                 int __ipmacc_tmp_i=0;
                                 //for(__ipmacc_tmp_i="""+range_low+"""+threadIdx.x; __ipmacc_tmp_i<("""+range_hig+"""); __ipmacc_tmp_i+=blockDim.x)
                                 for(__ipmacc_tmp_i=threadIdx.x+"""+range_low+"""; __ipmacc_tmp_i<("""+range_hig+"""); __ipmacc_tmp_i+=blockDim.x)  // we might use this line if the data is shared
                                 {
                                     """+vname+"""_sort_local[__ipmacc_tmp_i-"""+range_low+"""]="""+vname+"""[__ipmacc_tmp_i];
                                 }
                             }
                             __syncthreads();
                             // sort
                             //mergeSortSharedCall<"""+vtype_noptr+""">(&"""+vname+"""[0], blockDim.x, &__accelerator_compare1_"""+vtype_noptr+""", &__accelerator_compare2_"""+vtype_noptr+""");
                             //mergeSortSharedCall<"""+vtype_noptr+""">(&"""+vname+"""_sort_local[0], blockDim.x, &__accelerator_compare1_"""+vtype_noptr+""", &__accelerator_compare2_"""+vtype_noptr+""");
                             mergeSortSharedCall<"""+vtype_noptr+""">(&"""+vname+"""_sort_local[0], """+range_hig+'-'+range_low+""", &__accelerator_compare1_"""+vtype_noptr+""", &__accelerator_compare2_"""+vtype_noptr+""");
                             __syncthreads();
                             // writeback
                             {
                                 //if(threadIdx.x==0)
                                 {
                                     // only threadIdx.x==0 needs to have a copy of shared memory back.
                                    int __ipmacc_tmp_i=0;
                                    for(__ipmacc_tmp_i="""+range_low+"""; __ipmacc_tmp_i<("""+range_hig+"""); __ipmacc_tmp_i+=1)
                                    //for(__ipmacc_tmp_i=threadIdx.x+"""+range_low+"""; __ipmacc_tmp_i<("""+range_hig+"""); __ipmacc_tmp_i+=blockDim.x) // we might use this line if the data is shared
                                    {
                                        """+vname+"""[__ipmacc_tmp_i]="""+vname+"""_sort_local[__ipmacc_tmp_i-"""+range_low+"""];
                                    }
                                 }
                             }
                             __syncthreads();
                          """
                    else:
                        # use the current scope of variable
                        decl =''
                        code+="""
                             // sort
                             mergeSortSharedCall<"""+vtype_noptr+""">("""+vname+""", """+range_hig+'-'+range_low+""", &__accelerator_compare1_"""+vtype_noptr+""", &__accelerator_compare2_"""+vtype_noptr+""");
                          """
                    sort_dev_fname = ''
                    sort_dev_prototype = ''
                    sort_dev_decl = ''
                return [decl, code]
            elif i0.strip()=='find':
                code=''
                code+="""// """+i3+"""\n"""
                findargs = i3.split(',') # FIXME: this stuck on complex range specifiers, like (suba[0:foo(1,2,3)],subb[0:foo(3,4,5)])
                subarray = findargs[0]
                vname  = subarray.split('[')[0]
                config = subarray.split('[')[1].split(']')[0]
                range_low = config.split(':')[0]
                range_hig = config.split(':')[1]
                searchkey = findargs[1]
                searchret = findargs[2]

                try:
                    varNameList=self.oacc_kernelsLocalVarNams[kernelId]+self.oacc_kernelsVarNams[kernelId]
                    varTypeList=self.oacc_kernelsLocalVarTyps[kernelId]+self.oacc_kernelsVarTyps[kernelId]
                    vtype = varTypeList[varNameList.index(vname)]
                except:
                    print 'error: unable to specify the type of variable in algorithm directive: '+vname
                    print 'aborting()'
                    exit(-1)
                vtype_ispointer = vtype.count('*')
                if vtype_ispointer!=1:
                    print 'error: only single dimensional find is supported!'
                    print 'aborting()'
                    exit(-1)
                vtype_noptr = vtype.replace('*','')
                self.oacc_algoFind_Types2Overload.append(vtype_noptr)
                code+="""// """+vname+"""\n"""
                code+="""// """+vtype+"""\n"""
                code+="""// """+config+"""\n"""
                code+="""// """+range_low+"""\n"""
                code+="""// """+range_hig+"""\n"""
                code+="""// """+vtype_noptr+"""\n"""
                # remap the variable to __shared__ scope
                #bdx = self.oacc_kernelsConfig[kernelId]['blockDimx']
                #bdy = self.oacc_kernelsConfig[kernelId]['blockDimy']
                #bdz = self.oacc_kernelsConfig[kernelId]['blockDimz']
                [nctadim, bdx, bdy, bdz]=self.oacc_kernelsConfig_getDecl(kernelId)
                try:
                    bdx_i = int(bdx)
                    bdy_i = int(bdy)
                    bdz_i = int(bdz)
                except:
                    print 'warning: cannot specify the value of vector clause statically, nvcc may fail to compile the code.'
                if bdy=='1' and bdz=='1':
                    offset = '0'
                else:
                    offset = '((blockDim.y*threadIdx.z+threadIdx.y)*)'
                #_find_global_size = '('+bdy+')*('+bdz+')*('+range_hig+'-'+range_low+')'
                _find_global_size = '1' # total shared memory allocated per thread block
                _find_global_size_in_bytes = '('+_find_global_size+')*sizeof('+vtype_noptr+')' # total shared memory allocated per thread block
                _find_local_size  = '1' # size of shared memory independently processed
                self.cuda_shared_memory_dynamic_alloc.append(_find_global_size_in_bytes)
                _find_local_offset = '(blockDim.y*threadIdx.z+threadIdx.y)*('+_find_local_size+')'
                decl ='extern __shared__ '+vtype_noptr+' __ptr_dynamic_shared_allocation[];\n' #FIXME: SHOULD BE MOVED earlier in the kernel
                #decl+=vtype_noptr+' *'+vname+'_find_localcache = ('+vtype_noptr+'*)&__ptr_dynamic_shared_allocation['+_find_local_offset+'];\n'
                decl+='int *'+vname+'_find_localcache = (int*)&__ptr_dynamic_shared_allocation['+_find_local_offset+'];\n'
                decl+='// initialize the '+vname+'_find_localcache array'
                _init_value='-1' #'1<<30'
                decl+="""
                      {
                         if(threadIdx.x){"""+vname+"""_find_localcache[0] = """+_init_value+""";}
                      }
                      """
                code+="""// find
                     """+searchret+""" = algorithmFind<"""+vtype_noptr+""">("""+','.join([vname, range_low, range_hig, searchkey, vname+"_find_localcache[0]"])+""");
                  """
                return [decl, code]
            else:
                print 'unimplemented atomic clause: '+algoClause
                exit(-1)


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
        codeC+='extern cl_command_queue __ipmacc_temp_cmdqueue;\n'
        return codeC

    def syncDevice_opencl(self):
        code=''
        code+='if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\\n");\n'
        code+='clFinish(__ipmacc_temp_cmdqueue);\n'
        if USEAPI: code+='acc_training_kernel_end();\n'
        #code+='clFinish(__ipmacc_command_queue);\n'
        return code

    def openCondition_opencl(self,cond):
        return 'if('+cond+'){\n'

    def closeCondition_opencl(self,cond):
        return '}\n'

    def appendKernelToCode_opencl(self, kerPro, kerDec, kerId, forDims, args, smcinfo):
        ##self.code=kerPro+self.code+kerDec
        #blockDim=self.blockDim_opencl
        ##gridDim='('+'*'.join(forDims)+')/256+1'
        #gridDim='(('+forDims+'/'+blockDim+')+1)*'+blockDim
        [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kerId)
        if nctadim>1 or GENMULTIDIMTB:
            if DEBUGMULTIDIMTB:
                print 'injecting thread-block code:'
            dim3_gridblock ='size_t __ipmacc_gridDim[3]={1,1,1};\n'
            dim3_gridblock+='size_t __ipmacc_blockDim[3]={1,1,1};\n'
            dim3_gridblock+='size_t __ipmacc_offsets[3]={0,0,0};\n'
            dim3_gridblock+='uint __ipmacc_ndims='+str(len(forDims))+';\n'
            for f in range(0,len(forDims)):
                if forDims[f]=='':
                    break
                if   f==0:
                    ch='[0]'
                    dimension=ctadimx
                elif f==1:
                    ch='[1]'
                    dimension=ctadimy
                elif f==2:
                    ch='[2]'
                    dimension=ctadimz
                else:
                    print 'Error! Multi-dimensional grid is limited up to 3. Disable GENMULTIDIMTB in condegen.py'
                    exit(-1)
                #print ch+' '+dimension+' '+str(f)+' '+forDims[f]+' '+str(len(forDims))
                dim3_gridblock+='__ipmacc_blockDim'+ch+'='+dimension+';\n'
                #dim3_gridblock+='__ipmacc_blockDim.'+ch+'='+self.blockDim_cuda_xyz+';\n'
                padgrid='(((int)ceil('+forDims[f]+')%('+dimension+'))==0?0:1)'
                dim3_gridblock+='__ipmacc_gridDim'+ch+'=(int)((('+forDims[f]+')/__ipmacc_blockDim'+ch+')+('+padgrid+'))*'+'__ipmacc_blockDim'+ch+';\n'
            if DEBUGMULTIDIMTB:
                print dim3_gridblock
        else:
            blockDim=ctadimx #self.blockDim_cuda
            padgrid='(((int)ceil('+forDims+')%('+blockDim+'))==0?0:1)'
            gridDim='(int)(('+forDims+')/'+blockDim+'+'+padgrid+')*'+blockDim

        #callArgs=[]
        #for i in args:
        #    argName=i.split(' ')
        #    argName=argName[len(argName)-1]
        #    callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName, self.oacc_kernelsAssociatedCopyIds[kerId]))
        # remove undefined declaration from __kernel in three steps: 1) append kernel to code, 2) parse it using cpp, 3) extract the kernel back
        cleanKerDec=''
        for [tp,incstm] in self.code_getAssignments(self.var_parseForYacc(self.code+'\n'+kerDec),['fcn']):
            #if incstm.strip()[0:8]=='__kernel':
            if incstm.strip()[0:100].find('__kernel')!=-1:
                cleanKerDec=incstm
                break
        if cleanKerDec=='':
            print 'Fatal internal error! unable to retrieve back the kernel!'
            exit(-1)
        # prepare the prototype of function called in the regions
        func_proto=self.codegen_getFuncProto('accel')
        # prepare the declaration of function called in the regions
        func_decl =self.codegen_getFuncDecls() #OPENCL
        #cleanKerDec=statmnts+kerDec
        kerId_str=str(kerId)
        # prepare non-standard types
        type_decls=''
        #[intV, intT]=srcml_get_var_details(srcml_code2xml(cleanKerDec+'\n'+func_decl),'')
        #[intV, intT]=srcml_get_var_details(srcml_code2xml(cleanKerDec+'\n'+func_decl),self.prefix_kernel_gen+kerId_str)
        #print 'kernel#'+kerId_str+': '+','.join(intT)
        tmp_forwarddecl_proto=''
        for [nm, fwdcl, fudcl, oclfudcl, oclparent] in self.active_types_decl:
            tmp_active_flag = False
            for intTe in self.active_types:
                if intTe.find(nm)!=-1 or oclparent!='': #either type is used directly or indirectly
                    if DEBUGFWDCL: print 'type is active in this kernel: '+nm
                    type_decls+=oclfudcl+'\n'
                    tmp_forwarddecl_proto+=fwdcl+'\n'
                    tmp_active_flag = True
                    break
            if (not tmp_active_flag) and DEBUGFWDCL:
                print 'type is inactive in this kernel: '+nm
        type_decls = tmp_forwarddecl_proto + type_decls
        # renaming function calls within kernel
        # for [tmp_fname, tmp_prototype, tmp_declbody, tmp_rettype, tmp_qualifiers, tmp_params, tmp_local_vars, tmp_scope_vars, tmp_fcalls, tmp_ids, ex_params] in self.active_calls_decl:
        #     cleanKerDec=re.sub('\\b'+tmp_fname+'[\\ \\t\\n\\r]*\(','__accelerator_'+tmp_fname+'(', cleanKerDec)
        cleanKerDec = self.fix_call_args(cleanKerDec) # OPENCL

        # construct smc calls
        smc_select_calls=''
        if len(smcinfo)>0:
            print 'error: cache/smc is not implemented on OpenCL'
            print 'aborting()'
            exit(-1)
            if DEBUGSMC: print 'found smc clause'
            pfreelist=[]
            for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up] in smcinfo:
                fcall=self.prefix_kernel_smc_fetch+str(a)+'();'
                if cleanKerDec.find(fcall)==-1:
                    # this smc does not belong to this kernel, ignore
                    continue
                smc_select_calls+='// function identifier \n'+t.replace('*','')+' __smc_select_'+str(a)+'_'+v+'(int index, int down, int up, __global '+t+' g_array, __local '+t+' s_array, int vector_size, int pivot, int before){\n'
                if div=='false':
                    smc_select_calls+='// the pragmas are well-set. do not check the boundaries.\n'
                    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                else:
                    smc_select_calls+='// The tile is not well covered by the pivot, dw-range, and up-range\n'
                    smc_select_calls+='// dynamic runtime performs the check\n'
                    smc_select_calls+='short a=index>=down;\n'
                    smc_select_calls+='short b=index<up;\n'
                    smc_select_calls+='short d=a&b;\n'
                    smc_select_calls+='if(d){\n'
                    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                    smc_select_calls+='}\n'
                    smc_select_calls+='return g_array[index];\n'
                smc_select_calls+='}\n'
                pfreelist.append(a)
            for ids in pfreelist:
                fcallst=self.prefix_kernel_smc_fetch+str(ids)+'();'
                fcallen=self.prefix_kernel_smc_fetchend+str(ids)+'();'
                cleanKerDec=cleanKerDec.replace(fcallst,'')
                cleanKerDec=cleanKerDec.replace(fcallen,'')
        # append types, prototypes, and declarations to the kernel string
        cleanKerDec=type_decls+'\n'+func_proto+'\n'+func_decl+'\n'+smc_select_calls+'\n'+cleanKerDec
        # prepare the string
        cleanKerDec=cleanKerDec.replace('"','\"')
        cleanKerDec=cleanKerDec.replace('\n','\\\n')
        kernelInvoc='\n/* kernel call statement*/\n'
        kernelInvoc+='static cl_kernel __ipmacc_clkern'+kerId_str+'=NULL;\n'
        kernelRandomId=str(randint(1,10000000))
        if USEAPI:
            extensionSupports='#ifdef cl_khr_fp64\\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\\n#elif defined(cl_amd_fp64)\\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\\n#else\\n#error \\"Double precision floating point not supported by OpenCL implementation.\\"\\n#endif\\n'
            kernelInvoc+='const char* kernelSource'+kerId_str+' ="'+extensionSupports+cleanKerDec+'";\n'
            kernelInvoc+="__ipmacc_clkern"+kerId_str+"=(cl_kernel)acc_training_kernel_add(kernelSource"+kerId_str+", (char*)\" \", (char*)\""+self.prefix_kernel_gen+str(kerId_str)+"\","+kernelRandomId+", "+str(len(args))+");\n"
        else:
            kernelInvoc+='if( __ipmacc_clkern'+kerId_str+'==NULL){\n'
            extensionSupports='#ifdef cl_khr_fp64\\n#pragma OPENCL EXTENSION cl_khr_fp64 : enable\\n#elif defined(cl_amd_fp64)\\n#pragma OPENCL EXTENSION cl_amd_fp64 : enable\\n#else\\n#error \\"Double precision floating point not supported by OpenCL implementation.\\"\\n#endif\\n'
            kernelInvoc+='const char* kernelSource'+kerId_str+' ="'+extensionSupports+cleanKerDec+'";\n'
            kernelInvoc+='cl_program __ipmacc_clpgm'+kerId_str+';\n'
            kernelInvoc+='__ipmacc_clpgm'+kerId_str+'=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource'+kerId_str+', NULL, &__ipmacc_clerr);\n'
            kernelInvoc+=self.checkCallError_opencl('clCreateProgramWithSource','')
            kernelInvoc+='char __ipmacc_clcompileflags'+kerId_str+'[128];\n'
            kernelInvoc+='sprintf(__ipmacc_clcompileflags'+kerId_str+', " ");\n'
            #kernelInvoc+='sprintf(__ipmacc_clcompileflags'+kerId_str+', "-cl-mad-enable");\n'
            exceptionHandler="""
            size_t log_size=1024;
            char *build_log=NULL;
            __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm"""+kerId_str+""", __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
            if(__ipmacc_clerr!=CL_SUCCESS){
                printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\\n",__ipmacc_clerr);
            }
            build_log = (char*)malloc((log_size+1));
            // Second call to get the log
            __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm"""+kerId_str+""", __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
            if(__ipmacc_clerr!=CL_SUCCESS){
                printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\\n",__ipmacc_clerr);
            }
            build_log[log_size] = '\\0';
            printf("--- Build log (%d)---\\n ",log_size);
            fprintf(stderr, "%s\\n", build_log);
            free(build_log);"""
            kernelInvoc+='__ipmacc_clerr=clBuildProgram(__ipmacc_clpgm'+kerId_str+', 0, NULL, __ipmacc_clcompileflags'+kerId_str+', NULL, NULL);\n'
            kernelInvoc+=self.checkCallError_opencl('clBuildProgram',exceptionHandler)
            #kernelInvoc+='cl_kernel __ipmacc_clkern'+kerId_str+' = clCreateKernel(__ipmacc_clpgm'+kerId_str+', "'+self.prefix_kernel_gen+str(kerId_str)+'", &__ipmacc_clerr);\n'
            kernelInvoc+='__ipmacc_clkern'+kerId_str+' = clCreateKernel(__ipmacc_clpgm'+kerId_str+', "'+self.prefix_kernel_gen+str(kerId_str)+'", &__ipmacc_clerr);\n'
            kernelInvoc+=self.checkCallError_opencl('clCreateKernel','')
            kernelInvoc+='}\n'
        
        atomicRegion=False
        for j in range(0,len(args)):
            if args[j].find(self.prefix_kernel_atomicLocks)!=-1:
                atomicRegion=True
        if atomicRegion:
            atomicCodePreKernel=self.atomicRegion_locktype+' '+self.prefix_kernel_atomicLocks+'['+str(self.atomicRegion_nlocks)+']={'+', '.join('0'*self.atomicRegion_nlocks)+'};\n'
            atomicCodePreKernel+='acc_pcopyin((void*)'+self.prefix_kernel_atomicLocks+',10*sizeof('+self.atomicRegion_locktype+'));\n'
            atomicCodePostKernel=''
        else:
            atomicCodePreKernel=''
            atomicCodePostKernel=''
        for j in range(0,len(args)):
            pointer=(args[j].find('*')!=-1)
            argName=args[j].split(' ')[-1]
            if argName.find('__ipmacc_scalar')!=-1:
                argName='&'+argName
            argName=argName.replace('__ipmacc_scalar','')
            if argName.find('__ipmacc_reductionarray_internal')!=-1:
                argName=self.prefix_kernel_reduction_array+argName
            #argName=args[j].split(' ')[-1].replace('__ipmacc_reductionarray_internal','')
            argName=argName.replace('__ipmacc_reductionarray_internal','')
            argName=argName.replace('__ipmacc_opt_readonlycache','')
            #for singleArg in args[j].split(' ')[0:-1]:
            #    if singleArg!='static':
            #        argType+=singleArg+' '
            argType=' '.join(args[j].split(' ')[0:-1])
            #callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName, self.oacc_kernelsAssociatedCopyIds[kerId]))
            dname=self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName, self.oacc_kernelsAssociatedCopyIds[kerId])
            if pointer:
                # TODO kernelInvoc+='__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern'+kerId_str+', '+str(j)+', sizeof(cl_mem), (void *)&'+dname+');\n'
                if argName.find('__ipmacc_deviceptr')==-1:
                    kernelInvoc+='{\ncl_mem ptr=(cl_mem)acc_deviceptr('+argName+');\n__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern'+kerId_str+', '+str(j)+', sizeof(cl_mem), (void *)&ptr);\n}\n'
                else:
                    kernelInvoc+='{\ncl_mem ptr=(cl_mem)'+argName+';\n__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern'+kerId_str+', '+str(j)+', sizeof(cl_mem), (void *)&ptr);\n}\n'
            else:
                #kernelInvoc+='__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern'+kerId_str+', '+str(j)+', sizeof('+argType.replace('*','')+'), (void *)&'+dname+');\n'
                kernelInvoc+='{\n'+argType.replace('*','')+' immediate='+argName+';\n__ipmacc_clerr=clSetKernelArg(__ipmacc_clkern'+kerId_str+', '+str(j)+', sizeof('+argType.replace('*','')+'), (void *)&immediate);\n}\n'
            kernelInvoc+=self.checkCallError_opencl('clSetKernelArg','')
        if nctadim>1 or GENMULTIDIMTB:
            kernelInvoc+=dim3_gridblock
            kernelInvoc+=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel '+kerId_str+' > gridDim: (%d,%d,%d)\\tblockDim: (%d,%d,%d)\\n",__ipmacc_gridDim[0], __ipmacc_gridDim[1], __ipmacc_gridDim[2], __ipmacc_blockDim[0], __ipmacc_blockDim[1], __ipmacc_blockDim[2]);\n')
            kernelInvoc+='size_t *global_item_size'+kerId_str+' = __ipmacc_gridDim;\n'
            kernelInvoc+='size_t *local_item_size'+kerId_str+' = __ipmacc_blockDim;\n'
            kernelInvoc+='__ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue('+kernelRandomId+');\n'
            if USEAPI: kernelInvoc+='acc_training_kernel_start('+kernelRandomId+');\n'
            kernelInvoc+='__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_temp_cmdqueue, __ipmacc_clkern'+kerId_str+', __ipmacc_ndims, __ipmacc_offsets,\n global_item_size'+kerId_str+', local_item_size'+kerId_str+', 0, NULL, NULL);\n'
        else:
            kernelInvoc+='size_t global_item_size'+kerId_str+' = '+gridDim+';\n'
            kernelInvoc+='size_t local_item_size'+kerId_str+' = '+blockDim+';\n'
            kernelInvoc+=('if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel '+kerId_str+' > gridDim: %llu\\tblockDim: %llu\\n", global_item_size'+kerId_str+', local_item_size'+kerId_str+');\n')
            kernelInvoc+='__ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue('+kernelRandomId+');\n'
        #kernelInvoc+='cl_command_queue __ipmacc_temp_cmdqueue=(cl_command_queue)acc_training_decide_command_queue('+kernelRandomId+');\n'
            if USEAPI: kernelInvoc+='acc_training_kernel_start('+kernelRandomId+');\n'
            kernelInvoc+='__ipmacc_clerr=clEnqueueNDRangeKernel(__ipmacc_temp_cmdqueue, __ipmacc_clkern'+kerId_str+', 1, NULL,\n &global_item_size'+kerId_str+', &local_item_size'+kerId_str+', 0, NULL, NULL);\n'
        kernelInvoc+=self.checkCallError_opencl('clEnqueueNDRangeKernel','')
        #kernelInvoc+=self.prefix_kernel_gen+str(kerId)+'<<<'+gridDim+','+blockDim+'>>>('+(','.join(callArgs))+');'
        kernelInvoc+='\n/* kernel call statement*/\n'
        #self.code=self.code.replace(self.prefix_kernel+kerId_str+'();',kernelInvoc)
        self.code_kernels.append('\n{\n'+atomicCodePreKernel+kernelInvoc+atomicCodePostKernel+'\n}\n')


    def reduceVariable_opencl(self, var, type, op, ctasize, nesteddepth):
        arrname=self.prefix_kernel_reduction_shmem+var
        iterator=self.prefix_kernel_reduction_iterator
        code ='\n/* reduction on '+var+' */\n'
#        code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'
#        code+=arrname+'[get_local_id(0)]='+var+';\n';
#        code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'
#
        code+="""int __ctadimx=get_local_size(0);
               if(get_group_id(0)==(get_num_groups(0)-1)){
                   __local bool flag;
                   int begin=0, end=get_local_size(0);
                   while(true){
                       int newend = (end+begin)>>1;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       flag=false;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(get_local_id(0)>=newend)
                           flag=true;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimx=begin+1;
                           break;
                       }
                   }
               }
               int __ctadimy=get_local_size(1);
               if(get_group_id(1)==(get_num_groups(1)-1)){
                   __local bool flag;
                   int begin=0, end=get_local_size(1);
                   while(true){
                       int newend = (end+begin)>>1;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       flag=false;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(get_local_id(1)>=newend)
                           flag=true;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimy=begin+1;
                           break;
                       }
                   }
               }
               int __ctadimz=get_local_size(2);
               if(get_group_id(2)==(get_num_groups(2)-1)){
                   __local bool flag;
                   int begin=0, end=get_local_size(2);
                   while(true){
                       int newend = (end+begin)>>1;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       flag=false;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(get_local_id(2)>=newend)
                           flag=true;
                       barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);
                       if(flag){
                           begin=newend;
                       }else{
                           end=newend;
                       }
                       if((end-begin+1)==2){
                           __ctadimz=begin+1;
                           break;
                       }
                   }
               }\n"""
        code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'
        if   nesteddepth=='0':
            code+='unsigned int uniqueflat_local_id=get_local_id(0)+get_local_id(1)*(__ctadimx)+get_local_id(2)*(__ctadimx*__ctadimy);\n'
            code+=arrname+'[uniqueflat_local_id]='+var+';\n';
        elif nesteddepth=='1':
            code+='unsigned int uniquerow_local_id=get_local_id(2);\n'
            code+='unsigned int uniquecol_local_id=get_local_id(0)+get_local_id(1)*(__ctadimx);\n'
            code+=arrname+'[uniquerow_local_id][uniquecol_local_id]='+var+';\n';
        elif nesteddepth=='2':
            code+='unsigned int uniquerow_local_id=get_local_id(1)+get_local_id(2)*(__ctadimy);\n'
            code+='unsigned int uniquecol_local_id=get_local_id(0);\n'
            code+=arrname+'[uniquerow_local_id][uniquecol_local_id]='+var+';\n';
        else:
            print 'unsupported reduction configuration!'
            exit(-1)
        #code+='//printf("%dx%dx%d %dx%dx%d %d\\n",blockIdx.x,blockIdx.y,blockIdx.z,__ctadimx,__ctadimy,__ctadimz,uniqueflat_local_id);\n'
        code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'

        # ALTERIMPLEMENTATION
        # ALTER 1 
        #code+='for('+iterator+'='+ctasize+'; '+iterator+'>1; '+iterator+'='+iterator+'/2){\n'
        #code+='if(get_local_id(0)<'+iterator+' && get_local_id(0)>='+iterator+'/2){\n'
        #des=arrname+'[get_local_id(0)-('+iterator+'/2)]'
        #src=arrname+'[get_local_id(0)]'
        #if op=='min':
        #    code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        #elif op=='max':
        #    code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        #else:
        #    code+=des+'='+des+op+src+';\n'
        #code+='}\n'
        #code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'
        #code+='}\n'
        # ALTER 2
        if nesteddepth=='0':
            src=arrname+'[uniqueflat_local_id+'+iterator+']'
            des=arrname+'[uniqueflat_local_id]'
            code+='unsigned int reduction_length=__ctadimx*__ctadimy*__ctadimz;\n'
            code+='unsigned int startpoint=1<<(32-clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(uniqueflat_local_id<'+iterator+' && (uniqueflat_local_id+'+iterator+')<reduction_length){\n'
        elif nesteddepth=='1':
            src=arrname+'[rowid][colid+'+iterator+']'
            des=arrname+'[rowid][colid]'
            code+='unsigned int nrows=__ctadimz;\n'
            code+='unsigned int ncols=__ctadimx*__ctadimy;\n'
            code+='unsigned int colid=get_local_id(0)+get_local_id(1)*__ctadimx;\n'
            code+='unsigned int rowid=get_local_id(2);\n'
            code+='unsigned int reduction_length=ncols;\n'
            code+='unsigned int startpoint=1<<(32-clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(colid<'+iterator+' && (colid+'+iterator+')<reduction_length && colid<ncols && rowid<nrows){\n'
        elif nesteddepth=='2':
            src=arrname+'[rowid][colid+'+iterator+']'
            des=arrname+'[rowid][colid]'
            code+='unsigned int nrows=__ctadimz*__ctadimy;\n'
            code+='unsigned int ncols=__ctadimx;\n'
            code+='unsigned int colid=get_local_id(0);\n'
            code+='unsigned int rowid=get_local_id(1)+get_local_id(2)*__ctadimy;\n'
            code+='unsigned int reduction_length=ncols;\n'
            code+='unsigned int startpoint=1<<(32-clz(reduction_length));\n'
            code+='for('+iterator+'=(startpoint)/2;'+iterator+'>0; '+iterator+'>>=1) {\n'
            code+='if(colid<'+iterator+' && (colid+'+iterator+')<reduction_length && colid<ncols && rowid<nrows){\n'
        else:
            print 'unsupported reduction configuration!'
            exit(-1)
        if op=='min':
            code+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
        elif op=='max':
            code+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
        else:
            code+=des+'='+des+op+src+';\n'
        code+='}\n'
        code+='barrier(CLK_LOCAL_MEM_FENCE /*| CLK_GLOBAL_MEM_FENCE*/);\n'
        code+='}\n'
        # END OF ALTER


        code+='}// the end of '+var+' scope\n'
        # this reduction works for most devices, but can be implemented efficienctly considering device specific atomic operations
        #code+='/*atomicAdd('+var+','+var+'[0]+'+arrname+'[0]);\n\n*/'
        code+='if(get_local_id(0)==0 && get_local_id(1)==0 && get_local_id(2)==0){\n'
        if REDUCTION_TWOLEVELTREE:
            if nesteddepth=='0':
                code+=var+'__ipmacc_reductionarray_internal[get_group_id(0)+get_group_id(1)*(get_num_groups(0))+get_group_id(2)*(get_num_groups(0)*get_num_groups(1))]='+arrname+'[0];\n'
            else:
                code+=var+'__ipmacc_reductionarray_internal[get_group_id(0)+get_group_id(1)*(get_num_groups(0))+get_group_id(2)*(get_num_groups(0)*get_num_groups(1))]='+arrname+'[0][0];\n'
        else:
            print 'error: alternative reduction is not supported on OpenCL!'
            print '\tset REDUCTION_TWOLEVELTREE to True in codegen.py'
            exit(-1)
        code+='}\n'
        return code

    def constructKernel_opencl(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, template, smcinfo, compInfo):
        [nctadim, ctadimx, ctadimy, ctadimz]=ctasize
        code =template+' __kernel void '+self.prefix_kernel_gen+str(kernelId)
        suff_args=[]
        for idx in range(0,len(args)):
            sc=args[idx].replace('__ipmacc_deviceptr','')
            if self.opt_readonlycache:
                sc=sc.replace('__ipmacc_opt_readonlycache','') # FIXME fix this to add opencl support
            else:
                sc=sc.replace('__ipmacc_opt_readonlycache','')
            if sc.count('*')!=0:
                suff_args.append('__global '+sc)
            else:
                suff_args.append(sc)
        code+='('+','.join(suff_args)+')'
        proto=code+';\n'
        code+='{\n'
        code+='int '+self.prefix_kernel_uid_x+'=get_global_id(0);\n'
        code+='int '+self.prefix_kernel_uid_y+'=get_global_id(1);\n'
        code+='int '+self.prefix_kernel_uid_z+'=get_global_id(2);\n'
        if self.opt_readonlycache:
            readOnlyNotSupported = True #FIXME fix this to add opencl support
        # fetch __ipmacc_scalar into register
        # declare guard variable 
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                type=sc.replace(vname,'').replace('*','')
                code+=type+' '+vname.replace('__ipmacc_scalar','')+' = '+vname+'[0];\n'
                code+='bool '+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard = false;\n'
        #code+='if('+self.prefix_kernel_uid_x+'>='+forDims+'){\nreturn;\n}\n'
        if len(reduinfo+privinfo)>0:
            # 1) serve privates
            pfreelist=[]
            for [v, i, o, a, t, depth] in privinfo:
                fcall=self.prefix_kernel_privred_region+str(a)+'();'
                scp=('{ //start of reduction region for '+v+' \n') if o!='U' else ''
                kernelB=kernelB.replace(fcall,scp+t+' '+v+'='+i+';\n'+fcall)
                pfreelist.append(a)
            for ids in pfreelist:
                fcall=self.prefix_kernel_privred_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'');
            # 2) serve reductions
            decl+='int '+self.prefix_kernel_reduction_iterator+'=0;\n'
            #types=[] # types to reserve space for fast shared-memory reductions
            rfreelist=[] #remove reduction calls
            reduinfo.reverse()
            for [v, i, o, a, t, depth] in reduinfo:
                fcall=self.prefix_kernel_reduction_region+str(a)+'();'
                # 2) 1) append proper reduction code for this variable
                kernelB=kernelB.replace(fcall,self.codegen_reduceVariable(v,t,o,ctasize,depth)+fcall)
                #types.append(t)
                rfreelist.append(a)
                decl+=t+' '+v+';'
            reduinfo.reverse()
            # 2) 2) allocate shared memory reduction array
            #types=list(set(types))
            for [v, i, o, a, t, depth] in reduinfo:
            #for t in types:
                #code=code+'__local '+t+' '+self.prefix_kernel_reduction_shmem+t+'['+ctasize+'];\n'
                neutralvalue=self.get_neutralValueForOperation(o)
                if not(ctadimx.isdigit() and ctadimy.isdigit() and ctadimz.isdigit()):
                    print 'error: thread block dimension should be fixed for reduction!\n\tuse vector clause over loop directives to fix it.'
                    exit(-1)
                if depth=='0':
                    code=code+'__local '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimx,ctadimy,ctadimz])+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(0)+get_local_id(1)*get_local_size(0)+get_local_id(2)*(get_local_size(0)*get_local_size(1))]='+neutralvalue+';\n'
                    code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                elif depth=='1':
                    code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+ctadimz+']['+'*'.join([ctadimx,ctadimy])+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(2)][get_local_id(0)+get_local_id(1)*get_local_size(0)]='+neutralvalue+';\n'
                    code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                elif depth=='2':
                    code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimy,ctadimz])+']['+ctadimx+'];\n'
                    code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(1)+get_local_id(2)*get_local_size(1)][get_local_id(0)]='+neutralvalue+';\n'
                    code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                else:
                    print 'unsupported reduction configuration!'

            rfreelist=list(set(rfreelist))
            # 2) 3) free remaining fcalls
            for ids in rfreelist:
                fcall=self.prefix_kernel_reduction_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'')
        atomicBlocks=[]
        for [atomicKId, atomicId, atomicBody, atomicClause] in self.oacc_atomicReg:
            if atomicKId == kernelId:
                atomicBlocks.append([atomicId, atomicBody, atomicClause])
        if len(atomicBlocks)>0:
            lockindex=0
            for [atomicId, atomicBody, atomicClause] in atomicBlocks:
                kernelB=kernelB.replace(self.prefix_kernel_atomicRegion+str(atomicId)+'();\n'+atomicBody,'\n'+self.codegen_atomic(atomicBody, atomicClause, kernelId, lockindex)+'\n\n')
                lockindex+=1
        smc_select_calls=''
        if len(smcinfo)>0:
            print 'error: cache/smc directive is not implemented on OpenCL!'
            print 'aborting()'
            exit(-1)
            #pfreelist=[]
            #for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up] in smcinfo:
            for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up, dim2low, dim2high, pivot2, dw2range, up2range, w_dw2range, w_up2range, vcode] in smcinfo:
                if dim2low!='' and dim2high!='':
                    print 'two dimensional smc is not implemented on OpenCL.'
                    print 'aborting()'
                    exit(-1)
                fcall=self.prefix_kernel_smc_fetch+str(a)+'();'
                if kernelB.find(fcall)==-1:
                    # this smc does not belong to this kernel, ignore 
                    continue
                length=self.blockDim_opencl+'+'+dw+'+'+up
                decl+='\n/* declare the local memory of '+v+' */\n'
                decl+='__local '+t.replace('*','')+' '+self.prefix_kernel_smc_varpref+v+'['+length+'];\n'
                decl+='__local unsigned char '+self.prefix_kernel_smc_tagpref+v+'['+length+'];\n'
                decl+='{\n'
                decl+='int iterator_of_smc=0;\n'
                decl+='for(iterator_of_smc=get_local_id(0); iterator_of_smc<('+length+'); iterator_of_smc+=get_local_size(0)){\n'
                decl+='// '+self.prefix_kernel_smc_varpref+v+'[iterator_of_smc]=0;\n'
                decl+=self.prefix_kernel_smc_tagpref+v+'[iterator_of_smc]=0;\n'
                decl+='}\nbarrier(CLK_LOCAL_MEM_FENCE);\n'
                decl+='}\n'
                # fetch data to local memory
                datafetch ='{ // fetch begins\nint kk;\n'
                datafetch+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                datafetch+='for(int kk=get_local_id(0); kk<('+length+'); kk+=get_local_size(0))\n'
                datafetch+='{\n'
                datafetch+='int idx=get_group_id(0)*'+self.blockDim_opencl+'+kk-'+dw+'+'+p+';\n'
                datafetch+='if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
                datafetch+='{\n'
                datafetch+=self.prefix_kernel_smc_varpref+v+'[kk]='+v+'[idx];\n'
                datafetch+=self.prefix_kernel_smc_tagpref+v+'[kk]=1;\n'
                datafetch+='}\n'
                datafetch+='}\n'
                datafetch+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                datafetch+='} // end of fetch\n'
                datafetch+='#define '+v+'(index) __smc_select_'+str(a)+'_'+v+'(index, (get_group_id(0)*'+self.blockDim_opencl+')-('+dw+'), ((get_group_id(0)+1)*'+self.blockDim_opencl+')+('+up+'), '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_opencl+', '+p+', '+dw+')\n'
                kernelB=kernelB.replace(fcall,datafetch+'\n'+fcall)
                # construct the smc_select_ per array
                # following operations are performed in appendKernelToCode_opencl
                #smc_select_calls+='// function identifier \n'+t.replace('*','')+' __smc_select_'+str(a)+'_'+v+'(int index, int down, int up, '+t+' g_array, '+t+' s_array, int vector_size, int pivot, int before){\n'
                #if div=='false':
                #    smc_select_calls+='// the pragmas are well-set. do not check the boundaries.\n'
                #    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                #else:
                #    smc_select_calls+='// The tile is not well covered by the pivot, dw-range, and up-range\n'
                #    smc_select_calls+='// dynamic runtime performs the check\n'
                #    smc_select_calls+='short a=index>=down;\n'
                #    smc_select_calls+='short b=index<up;\n'
                #    smc_select_calls+='short d=a&b;\n'
                #    smc_select_calls+='if(d){\n'
                #    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                #    smc_select_calls+='}\n'
                #    smc_select_calls+='return g_array[index];\n'
                #smc_select_calls+='}\n'
                # replace array-ref [] with function call ()
                fcallst=self.prefix_kernel_smc_fetch+str(a)+'();'
                fcallen=self.prefix_kernel_smc_fetchend+str(a)+'();'
                changeRangeIdx_start=kernelB.find(fcallst)
                changeRangeIdx_end=kernelB.find(fcallen)
                #print kernelB[changeRangeIdx_start:changeRangeIdx_end]
                if (changeRangeIdx_start==-1 ) or (changeRangeIdx_end==-1) or (changeRangeIdx_start>changeRangeIdx_end):
                    print 'fatal error! could not determine the smc range for '+v
                    exit(-1)
                # for each arrayReference of 'v', replace [] with ()
                for arrayRef in re.finditer('\\b'+v+'[\\ \\t\\n\\r]*\[',kernelB[changeRangeIdx_start:changeRangeIdx_end]):
                    arrayRef_it=changeRangeIdx_start+arrayRef.start(0)
                    arrayRef_pcnt=0
                    done=False
                    while not done:
                        if kernelB[arrayRef_it]=='[':
                            if arrayRef_pcnt==0:
                                #kernelB[arrayRef_it]='('
                                kernelB=kernelB[:arrayRef_it]+'('+kernelB[arrayRef_it+1:]
                            arrayRef_pcnt+=1
                        elif kernelB[arrayRef_it]==']':
                            arrayRef_pcnt-=1
                            if arrayRef_pcnt==0:
                                #kernelB[arrayRef_it]=')'
                                kernelB=kernelB[:arrayRef_it]+')'+kernelB[arrayRef_it+1:]
                                done=True
                        arrayRef_it+=1
                     
                # undef function call ()
                kernelB=kernelB.replace(fcallen,'#undef '+v+'\n'+fcallen)
                #pfreelist.append(a)
            #for ids in pfreelist:
            #    fcallst=self.prefix_kernel_smc_fetch+str(ids)+'();'
            #    fcallen=self.prefix_kernel_smc_fetchend+str(ids)+'();'
            #    kernelB=kernelB.replace(fcallst,'')
            #    kernelB=kernelB.replace(fcallen,'')
        #print 'smc_select_calls:> '+smc_select_calls
        #code=smc_select_calls+'/* HOHA */\n'+code
        code+=decl
        # update the boolean guard for every writes to scalar variables
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                scalvname = vname.replace('__ipmacc_scalar','')
                kernelB = self.guard_write_to_scalar_variable(kernelB, scalvname)
        code+=kernelB
        code+='//append writeback of scalar variables\n'
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                code+='if('+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard'+'){\n'
                code+=vname+'[0]='+vname.replace('__ipmacc_scalar','')+';\n'
                code+='}\n'
        code+='}\n'
        return [proto, code]
    def memAlloc_opencl(self, var, size):
        codeM=var+' = clCreateBuffer(__ipmacc_clctx, CL_MEM_READ_WRITE, '+size+', NULL, &__ipmacc_clerr);\n'
        codeM+=self.checkCallError_opencl('clCreateBuffer','')
        return codeM
    def memCpy_opencl(self, des, src, size, type):
        if type=='in':
            codeC='clEnqueueWriteBuffer(__ipmacc_command_queue, '+des+', CL_TRUE, 0, '+size+','+src+', 0, NULL, NULL);\n'
            codeC+=self.checkCallError_opencl('clEnqueueWriteBuffer','')
        else:
            codeC='clEnqueueReadBuffer(__ipmacc_command_queue, '+src+', CL_TRUE, 0, '+size+','+des+', 0, NULL, NULL);\n'
            codeC+=self.checkCallError_opencl('clEnqueueReadBuffer','')
        return codeC
    def devPtrDeclare_opencl(self, type, name, sccopy):
        #return 'cl_mem'+('* ' if sccopy else ' ')+name+';\n'
        return 'cl_mem '+name+';\n'
    def checkCallError_opencl(self,fcn,expt):
        code ='if(__ipmacc_clerr!=CL_SUCCESS){\n'
        code+='printf("OpenCL Runtime Error in '+fcn+'! id: %d\\n",__ipmacc_clerr);\n'
        code+=expt
        code+='exit(-1);\n'
        code+='}\n'
        return code

    def atomic_opencl(self, atomicBody, atomicClause, kernelId, lockindex):
        lockvariable=self.prefix_kernel_atomicLocks+'['+str(lockindex)+']'
        if atomicClause=='capture':
            code="""{
                      bool __ipmacc_leaveLoop = false;
                      while (!__ipmacc_leaveLoop) {
                        if (atom_xchg(&("""+lockvariable+"""), 1u) == 0u) {
                          //critical section\n"""+atomicBody+"""\n
                          __ipmacc_leaveLoop = true;
                          atom_xchg(&("""+lockvariable+"""),0u);
                        }
                      }
                    } 
            """
            return code
        else:
            print 'unimplemented atomic clause: '+atomicClause
            exit(-1)

    # ispc platform
    def constructKernel_ispc(self, args, decl, kernelB, kernelId, privinfo, reduinfo, ctasize, forDims, template, smcinfo, compInfo):
        [nctadim, ctadimx, ctadimy, ctadimz]=ctasize
        code =template+'task void '+self.prefix_kernel_gen+str(kernelId)
        suff_args_proto=[]
        suff_args_code=[]
        suff_args_launch_call=[]
        for idx in range(0,len(args)):
            sc=args[idx].replace('__ipmacc_deviceptr','')
            if self.opt_readonlycache:
                sc=sc.replace('__ipmacc_opt_readonlycache','') # FIXME fix this to add ispc support
            else:
                sc=sc.replace('__ipmacc_opt_readonlycache','')
            suff_args_launch_call.append(sc.split()[-1])
            if sc.count('*')!=0:
                sc=sc.replace('*','')+sc.count('*')*'[]'
                suff_args_code.append('uniform '+sc)
                suff_args_proto.append(sc)
            else:
                suff_args_code.append('uniform '+sc)
                suff_args_proto.append(sc)
        code +='('+','.join(suff_args_code)+')'
        code+='{\n'
        code+='int '+self.prefix_kernel_uid_x+'=programIndex;\n'
        #code+='int '+self.prefix_kernel_uid_y+'=get_global_id(1);\n'
        #code+='int '+self.prefix_kernel_uid_z+'=get_global_id(2);\n'
        if self.opt_readonlycache:
            print 'warning: readonlycache is not implemented for ISPC.'
            readOnlyNotSupported = True #FIXME fix this to add ispc support
        # fetch __ipmacc_scalar into register
        for sc in args:
            # print 'warning: scalar is not implemented for ISPC.'
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                type=sc.replace(vname,'').replace('*','')
                code+=type+' '+vname.replace('__ipmacc_scalar','')+' = '+vname+'[0];\n'
                code+='bool '+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard = false;\n'
        #code+='if('+self.prefix_kernel_uid_x+'>='+forDims+'){\nreturn;\n}\n'
        if len(reduinfo+privinfo)>0:
            print 'warning: reduction/private is not implemented for ISPC.'
            # 1) serve privates
            pfreelist=[]
            for [v, i, o, a, t, depth] in privinfo:
                fcall=self.prefix_kernel_privred_region+str(a)+'();'
                scp=('{ //start of reduction region for '+v+' \n') if o!='U' else ''
                kernelB=kernelB.replace(fcall,scp+t+' '+v+'='+i+';\n'+fcall)
                pfreelist.append(a)
            for ids in pfreelist:
                fcall=self.prefix_kernel_privred_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'');
            # 2) serve reductions
            decl+='int '+self.prefix_kernel_reduction_iterator+'=0;\n'
            #types=[] # types to reserve space for fast shared-memory reductions
            rfreelist=[] #remove reduction calls
            reduinfo.reverse()
            for [v, i, o, a, t, depth] in reduinfo:
                fcall=self.prefix_kernel_reduction_region+str(a)+'();'
                # 2) 1) append proper reduction code for this variable
                kernelB=kernelB.replace(fcall,self.codegen_reduceVariable(v,t,o,ctasize,depth)+fcall)
                #types.append(t)
                rfreelist.append(a)
                decl+=t+' '+v+';'
            reduinfo.reverse()
            # 2) 2) allocate shared memory reduction array
            #types=list(set(types))
            #for [v, i, o, a, t, depth] in reduinfo:
            ##for t in types:
            #    #code=code+'__local '+t+' '+self.prefix_kernel_reduction_shmem+t+'['+ctasize+'];\n'
            #    neutralvalue=self.get_neutralValueForOperation(o)
            #    if not(ctadimx.isdigit() and ctadimy.isdigit() and ctadimz.isdigit()):
            #        print 'error: thread block dimension should be fixed for reduction!\n\tuse vector clause over loop directives to fix it.'
            #        exit(-1)
            #    if depth=='0':
            #        code=code+'__local '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimx,ctadimy,ctadimz])+'];\n'
            #        code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(0)+get_local_id(1)*get_local_size(0)+get_local_id(2)*(get_local_size(0)*get_local_size(1))]='+neutralvalue+';\n'
            #        code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
            #    elif depth=='1':
            #        code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+ctadimz+']['+'*'.join([ctadimx,ctadimy])+'];\n'
            #        code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(2)][get_local_id(0)+get_local_id(1)*get_local_size(0)]='+neutralvalue+';\n'
            #        code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
            #    elif depth=='2':
            #        code=code+'__shared__ '+t+' '+self.prefix_kernel_reduction_shmem+v+'['+'*'.join([ctadimy,ctadimz])+']['+ctadimx+'];\n'
            #        code+=self.prefix_kernel_reduction_shmem+v+'[get_local_id(1)+get_local_id(2)*get_local_size(1)][get_local_id(0)]='+neutralvalue+';\n'
            #        code+='barrier(CLK_LOCAL_MEM_FENCE);\n'
            #    else:
            #        print 'unsupported reduction configuration!'

            rfreelist=list(set(rfreelist))
            # 2) 3) free remaining fcalls
            for ids in rfreelist:
                fcall=self.prefix_kernel_reduction_region+str(ids)+'();'
                kernelB=kernelB.replace(fcall,'')
        atomicBlocks=[]
        for [atomicKId, atomicId, atomicBody, atomicClause] in self.oacc_atomicReg:
            if atomicKId == kernelId:
                atomicBlocks.append([atomicId, atomicBody, atomicClause])
        if len(atomicBlocks)>0:
            print 'warning: atomic is not implemented for ISPC.'
            lockindex=0
            for [atomicId, atomicBody, atomicClause] in atomicBlocks:
                kernelB=kernelB.replace(self.prefix_kernel_atomicRegion+str(atomicId)+'();\n'+atomicBody,'\n'+self.codegen_atomic(atomicBody, atomicClause, kernelId, lockindex)+'\n\n')
                lockindex+=1
        smc_select_calls=''
        if len(smcinfo)>0:
            print 'error: smc is not implemented for ISPC.'
            print 'aborting()'
            exit(-1)
            #pfreelist=[]
            for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up] in smcinfo:
                fcall=self.prefix_kernel_smc_fetch+str(a)+'();'
                if kernelB.find(fcall)==-1:
                    # this smc does not belong to this kernel, ignore 
                    continue
                length=self.blockDim_opencl+'+'+dw+'+'+up
                decl+='\n/* declare the local memory of '+v+' */\n'
                decl+='__local '+t.replace('*','')+' '+self.prefix_kernel_smc_varpref+v+'['+length+'];\n'
                decl+='__local unsigned char '+self.prefix_kernel_smc_tagpref+v+'['+length+'];\n'
                decl+='{\n'
                decl+='int iterator_of_smc=0;\n'
                decl+='for(iterator_of_smc=get_local_id(0); iterator_of_smc<('+length+'); iterator_of_smc+=get_local_size(0)){\n'
                decl+='// '+self.prefix_kernel_smc_varpref+v+'[iterator_of_smc]=0;\n'
                decl+=self.prefix_kernel_smc_tagpref+v+'[iterator_of_smc]=0;\n'
                decl+='}\nbarrier(CLK_LOCAL_MEM_FENCE);\n'
                decl+='}\n'
                # fetch data to local memory
                datafetch ='{ // fetch begins\nint kk;\n'
                datafetch+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                datafetch+='for(int kk=get_local_id(0); kk<('+length+'); kk+=get_local_size(0))\n'
                datafetch+='{\n'
                datafetch+='int idx=get_group_id(0)*'+self.blockDim_opencl+'+kk-'+dw+'+'+p+';\n'
                datafetch+='if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
                datafetch+='{\n'
                datafetch+=self.prefix_kernel_smc_varpref+v+'[kk]='+v+'[idx];\n'
                datafetch+=self.prefix_kernel_smc_tagpref+v+'[kk]=1;\n'
                datafetch+='}\n'
                datafetch+='}\n'
                datafetch+='barrier(CLK_LOCAL_MEM_FENCE);\n'
                datafetch+='} // end of fetch\n'
                datafetch+='#define '+v+'(index) __smc_select_'+str(a)+'_'+v+'(index, (get_group_id(0)*'+self.blockDim_opencl+')-('+dw+'), ((get_group_id(0)+1)*'+self.blockDim_opencl+')+('+up+'), '+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.blockDim_opencl+', '+p+', '+dw+')\n'
                kernelB=kernelB.replace(fcall,datafetch+'\n'+fcall)
                # replace array-ref [] with function call ()
                fcallst=self.prefix_kernel_smc_fetch+str(a)+'();'
                fcallen=self.prefix_kernel_smc_fetchend+str(a)+'();'
                changeRangeIdx_start=kernelB.find(fcallst)
                changeRangeIdx_end=kernelB.find(fcallen)
                #print kernelB[changeRangeIdx_start:changeRangeIdx_end]
                if (changeRangeIdx_start==-1 ) or (changeRangeIdx_end==-1) or (changeRangeIdx_start>changeRangeIdx_end):
                    print 'fatal error! could not determine the smc range for '+v
                    exit(-1)
                # for each arrayReference of 'v', replace [] with ()
                for arrayRef in re.finditer('\\b'+v+'[\\ \\t\\n\\r]*\[',kernelB[changeRangeIdx_start:changeRangeIdx_end]):
                    arrayRef_it=changeRangeIdx_start+arrayRef.start(0)
                    arrayRef_pcnt=0
                    done=False
                    while not done:
                        if kernelB[arrayRef_it]=='[':
                            if arrayRef_pcnt==0:
                                #kernelB[arrayRef_it]='('
                                kernelB=kernelB[:arrayRef_it]+'('+kernelB[arrayRef_it+1:]
                            arrayRef_pcnt+=1
                        elif kernelB[arrayRef_it]==']':
                            arrayRef_pcnt-=1
                            if arrayRef_pcnt==0:
                                #kernelB[arrayRef_it]=')'
                                kernelB=kernelB[:arrayRef_it]+')'+kernelB[arrayRef_it+1:]
                                done=True
                        arrayRef_it+=1
                     
                # undef function call ()
                kernelB=kernelB.replace(fcallen,'#undef '+v+'\n'+fcallen)
        code+=decl
        # update the boolean guard for every writes to scalar variables
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                scalvname = vname.replace('__ipmacc_scalar','')
                kernelB = self.guard_write_to_scalar_variable(kernelB, scalvname)
        code+=kernelB
        code+='//append writeback of scalar variables\n'
        for sc in args:
            if sc.find('__ipmacc_scalar')!=-1:
                vname=sc.split(' ')[-1]
                code+='if('+vname.replace('__ipmacc_scalar','')+'__ipmacc_guard'+'){\n'
                code+=vname+'[0]='+vname.replace('__ipmacc_scalar','')+';\n'
                code+='}\n'
        code+='}\n'
        code+=template
        code+="export void "+self.prefix_kernel_lau+str(kernelId)
        code+='('+','.join(suff_args_code)+')'
        code+="{"
        if nctadim>1:
            code+="launch [__ispc_n_threads] "+self.prefix_kernel_gen+str(kernelId)+"("+','.join(suff_args_launch_call)+");"
        else:
            code+="launch [1] "+self.prefix_kernel_gen+str(kernelId)+"("+','.join(suff_args_launch_call)+");"
        code+="}"
        proto=template+'extern "C" void '+self.prefix_kernel_lau+str(kernelId)
        proto+='('+','.join(suff_args_proto)+')'+';\n'
        return [proto, code]

    def appendKernelToCode_ispc(self, kerPro, kerDec, kerId, forDims, args, smcinfo):
        parallelizeovertask=False
        func_proto = self.codegen_getFuncProto(proto_format='host') # ISPC
        func_decl = '' # append them all once at the end (replacing self.codegen_getFuncDecls()) #ISPC
        self.code=self.code.replace(' __ipmacc_prototypes_kernels_'+str(kerId)+' ',' '+func_proto+kerPro+' \n')
        [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(kerId)
        if nctadim>1:
            parallelizeovertask=True
            print 'warning: multiple loops are parallelized under ispc! parallelizing inner over SIMD and outer over cores. '+str(getframeinfo(currentframe()).lineno)
            #print kerDec
            #exit(-1)

        # no need to adjust gang-size, proceed with implicit or compile-time configuration

        # remove undefined declaration from __kernel in three steps: 1) append kernel to code, 2) parse it using cpp, 3) extract the kernel back
        #print self.code+'\n'+kerDec
        cleanKerDec=''
        listOfFunctions = self.code_getAssignments(self.var_parseForYacc(self.code+'\n'+kerDec),['fcn'])
        for [tp,incstm] in listOfFunctions:
            #if incstm.strip()[0:8]=='__kernel':
            if incstm.strip()[0:100].find('task')!=-1:
                cleanKerDec+=incstm
                break
        for [tp,incstm] in listOfFunctions:
            #if incstm.strip()[0:8]=='__kernel':
            if incstm.strip()[0:100].find('export')!=-1:
                cleanKerDec+=incstm
                break
        if cleanKerDec=='':
            print self.code+'\n'+kerDec
            print 'Fatal internal error! unable to retrieve back the kernel! #'+str(getframeinfo(currentframe()).lineno)
            exit(-1)
        # prepare the prototype of function called in the regions
        # prepare the declaration of function called in the regions
        kerId_str=str(kerId)
        type_decls=''
        if DEBUGFWDCL:
            print str(len(self.active_types_decl))+' found to be undeclared (be appended.)'
        tmp_forwarddecl_proto=''
        for [nm, fwdcl, fudispc, ispcfudcl, ispcparent] in self.active_types_decl:
            #print 'warning: arbitrary type is not implemented for ISPC.'
            tmp_active_flag = False
            for intTe in self.active_types:
                if intTe.find(nm)!=-1 or ispcparent!='': #either type is used directly or indirectly
                    if DEBUGFWDCL: print 'type is active in this kernel: '+nm
                    type_decls+=ispcfudcl+'\n'
                    tmp_forwarddecl_proto+=fwdcl+'\n'
                    tmp_active_flag = True
                    break
            if (not tmp_active_flag) and DEBUGFWDCL:
                print 'type is inactive in this kernel: '+nm
        type_decls = tmp_forwarddecl_proto + type_decls
        # renaming function calls within kernel
        cleanKerDec = self.fix_call_args(cleanKerDec) # ISPC
        # construct smc calls
        smc_select_calls=''
        if len(smcinfo)>0:
            print 'error: smc is not implemented for ISPC.'
            print 'aborting()'
            exit(-1)
            if DEBUGSMC: print 'found smc clause'
            pfreelist=[]
            for [v, t, st, p, dw, up, div, a, dimlo, dimhi, w_dw, w_up] in smcinfo:
                fcall=self.prefix_kernel_smc_fetch+str(a)+'();'
                if cleanKerDec.find(fcall)==-1:
                    # this smc does not belong to this kernel, ignore
                    continue
                smc_select_calls+='// function identifier \n'+t.replace('*','')+' __smc_select_'+str(a)+'_'+v+'(int index, int down, int up, __global '+t+' g_array, __local '+t+' s_array, int vector_size, int pivot, int before){\n'
                if div=='false':
                    smc_select_calls+='// the pragmas are well-set. do not check the boundaries.\n'
                    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                else:
                    smc_select_calls+='// The tile is not well covered by the pivot, dw-range, and up-range\n'
                    smc_select_calls+='// dynamic runtime performs the check\n'
                    smc_select_calls+='short a=index>=down;\n'
                    smc_select_calls+='short b=index<up;\n'
                    smc_select_calls+='short d=a&b;\n'
                    smc_select_calls+='if(d){\n'
                    smc_select_calls+='return s_array[index-(vector_size*get_group_id(0))+before-pivot];\n'
                    smc_select_calls+='}\n'
                    smc_select_calls+='return g_array[index];\n'
                smc_select_calls+='}\n'
                pfreelist.append(a)
            for ids in pfreelist:
                fcallst=self.prefix_kernel_smc_fetch+str(ids)+'();'
                fcallen=self.prefix_kernel_smc_fetchend+str(ids)+'();'
                cleanKerDec=cleanKerDec.replace(fcallst,'')
                cleanKerDec=cleanKerDec.replace(fcallen,'')
        # append types, prototypes, and declarations to the kernel string
        func_proto_accel = self.codegen_getFuncProto(proto_format='accel') # ISPC
        cleanKerDec=type_decls+'\n'+func_proto_accel+'\n'+func_decl+'\n'+smc_select_calls+'\n'+cleanKerDec+'\n'
        self.ispc_kerneldecl+=cleanKerDec
        #print 'clean kernel declaration:\n'+cleanKerDec
        # prepare the sting
        #cleanKerDec=cleanKerDec.replace('"','\"')
        #cleanKerDec=cleanKerDec.replace('\n','\\n')

        callArgs=[]
        atomicRegion=False
        for i in args:
            argName=i.split(' ')
            argType=''
            if i.find(self.prefix_kernel_atomicLocks)!=-1:
                if DEBUGATOMIC: print 'atomic variable: '+i
                atomicRegion=True
            #for singleArg in argName:
            #    if singleArg!='static':
            #        argType+=singleArg+' '
            argType=' '.join(argName[0:len(argName)-1])
            argName=argName[len(argName)-1]
            if argName.find('__ipmacc_scalar')!=-1:
                argName='&'+argName.replace('__ipmacc_scalar','')
            if argName.find('__ipmacc_reductionarray_internal')!=-1:
                argName=self.prefix_kernel_reduction_array+argName
                argName=argName.replace('__ipmacc_reductionarray_internal','')
            #TODO callArgs.append(self.varmapper_getDeviceName(self.oacc_kernelsParent[kerId], argName, self.oacc_kernelsAssociatedCopyIds[kerId]))
            argName=argName.replace('__ipmacc_opt_readonlycache','')
            if argName.find('__ipmacc_container')!=-1:
                print 'warning: container is not implemented for ISPC.'
                argName=argName.replace('__ipmacc_container','')
                callArgs.append( ('\n('+argType+')acc_deviceptr((void*)__ipmacc_contmap.get_buffer_ptr('+argName+'))') )
            elif argName.find('__ipmacc_deviceptr')!=-1:
                argName=argName.replace('__ipmacc_deviceptr','')
                callArgs.append( '\n'+argName)
            else:
                callArgs.append(argName)

        if atomicRegion:
            print 'warning: atomic is not implemented for ISPC.'
            atomicCodePreKernel=self.atomicRegion_locktype+' '+self.prefix_kernel_atomicLocks+'['+str(self.atomicRegion_nlocks)+']={'+', '.join('0'*self.atomicRegion_nlocks)+'};\n'
            atomicCodePreKernel+='acc_pcopyin((void*)'+self.prefix_kernel_atomicLocks+',10*sizeof('+self.atomicRegion_locktype+'));\n'
            atomicCodePostKernel=''
        else:
            atomicCodePreKernel=''
            atomicCodePostKernel=''
        kernelInvoc='\n/* kernel call statement*/\n{\n'
        #if parallelizeovertask:
        kernelInvoc+='\nunsigned int __ispc_n_threads = sysconf(_SC_NPROCESSORS_ONLN); // acc_get_n_cores(acc_device_intelispc);\n'
        kernelInvoc+='if(getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching ISPC kernel> %d threads + SIMD \\n", __ispc_n_threads);\n'
        #    kernelInvoc+='\nfor(unsigned int __ispc_thread_idx=0; __ispc_thread_idx<__ispc_n_threads; __ispc_thread_idx++){\n'
        kernelInvoc+=self.prefix_kernel_lau+str(kerId)+'('+','.join(callArgs)+');'
        #if parallelizeovertask:
        #    kernelInvoc+='\n}\n'
        kernelInvoc+='\n}\n/* kernel call statement*/\n'
        self.code=self.code.replace(self.prefix_kernel+str(kerId)+'();',atomicCodePreKernel+kernelInvoc+atomicCodePostKernel)
        self.code_kernels.append('\n{\n'+atomicCodePreKernel+kernelInvoc+atomicCodePostKernel+'\n}\n')
        #print self.code
    def includeHeaders_ispc(self):
        self.code_include+='// no header for ISPC\n'
    def generate_kernel_file_ispc(self):
        ispcfile='.'.join(self.foname.split('.')[0:-1])+'.ispc'
        print '  warning: storing ispc kernels in '+ispcfile
        f=open(ispcfile, 'w')
        #code=re.sub('\\b'+'int'+'[\\ \\t\\n\\r]*','int32 ', self.ispc_kerneldecl)
        code ='#define char int8\n'
        code+='#define fabsf(f) abs(f)\n'
        code+='#define floorf(f) floor(f)\n'
        code+='#define logf(f) log(f)\n'
        code+='#define sqrtf(f) sqrt(f)\n'
        code+='#define expf(f) exp(f)\n'
        code+='#define powf(f,p) pow(f,p)\n'
        code+=self.ispc_kerneldecl
        f.write(code)
        f.close()

    def reduceVariable_ispc(self, var, type, op, ctasize, nesteddepth):
        arrname=self.prefix_kernel_reduction_shmem+var
        iterator=self.prefix_kernel_reduction_iterator
        code ='\n/* reduction on '+var+' */\n'
        code +='{\n'

        #if nesteddepth=='0':
        #    print nesteddepth
        #else:
        #    print 'unsupported reduction configuration!'
        #    exit(-1)
        des=var+'__ipmacc_reductionarray_internal[0]'
        src=var
        if op=='min':
            code+=des+'=reduce_min('+src+');\n'
        elif op=='max':
            code+=des+'=reduce_max('+src+');\n'
        elif op=='+':
            code+=des+'=reduce_add('+src+');\n'
        else:
            print 'unsupported reduction operation!'
            exit(-1)
        code+='}\n'
        code+='}// the end of '+var+' scope\n'
        #print code
        return code


    # Marking for final replacement
    def mark_implicitcopy(self,inout,kid):
        return self.prefix_dataimpli+inout+str(kid)+'();'

    def scanner_xml2code(self, root):
        code = '' if str(root.text)=='None' else root.text
        for ch in root:
            code += self.scanner_xml2code(ch)
        #print code
        #exit(-1)
        return code

    #
    # Top Level Recursive Code Analyzer
    def code_descendentRetrieve(self, root, depth, associated_copy_ids):
        # parse the code's XML tree (root) and retrieve the intermediate code (self.code)
        scope_associated_copy_ids=[]
        scope_associated_copy_ids+=associated_copy_ids
        if root.tag == 'pragma' and root.attrib.get('directive')=='kernels':
            # case 1: start of the kernel region
            # parse the clause for data (including copy, copyin, copyout, create, and similar present alternatives
            expressionIn=''
            expressionAlloc=''
            expressionOut=''
            expressionAll=''
            copyoutId=-1
            [expressionIn, expressionAlloc, expressionOut, expressionAll] = self.oacc_clauseparser_data(str(root.attrib.get('clause')),str(self.oacc_copyId), False, False)
            if DEBUGVAR:
                print 'Kernels data clause: <'+expressionIn+'\n'+expressionAlloc+'\n'+expressionOut+'>' # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
                print 'all data clauses: <'+expressionAll+'>'
            # * generate proper code before the kernels region:
            #   - if
            regionCondition=self.oacc_clauseparser_if(str(root.attrib.get('clause')))
            if regionCondition!='':
                self.code=self.code+self.codegen_openCondition(regionCondition)
            #   - copy, copyin (allocation and transfer)
            #self.util_copyIdAppend(expressionIn, expressionAlloc, expressionOut, depth)
            copyoutId=self.util_copyIdAppend(expressionIn, expressionAlloc, expressionOut, depth, expressionAll)
            #print 'kernels: appending '+str(copyoutId)
            scope_associated_copy_ids+=[copyoutId]
            #   - track automatic vars (deviceptr)
            expressionDeviceptrs=self.oacc_clauseparser_deviceptr(str(root.attrib.get('clause')))
            if expressionDeviceptrs!='' or self.oacc_scopeAutomaPtr!='':
                # append in either case
                if DEBUGVAR:
                    print 'appending automatic vars: '+(expressionDeviceptrs+' '+self.oacc_scopeAutomaPtr).strip().replace(' ',',')
                self.oacc_kernelsAutomaPtrs.append((expressionDeviceptrs+' '+self.oacc_scopeAutomaPtr).strip().replace(' ',','))
            else:
                self.oacc_kernelsAutomaPtrs.append('')
            #   - track manual vars (copy in, copy out, and create)
            expressionManualVars=self.varname_extractor(expressionAll)
            #expressionManualVars=self.varname_extractor(expressionIn+'\n'+expressionOut+'\n'+expressionAlloc)
            if DEBUGVAR:
                print 'Extracted manual variable names > '+expressionManualVars
            if expressionManualVars!='' or self.oacc_scopeManualPtr!='':
                # append in either case
                if DEBUGCP>1:
                    print 'kernelManualPtrs: '+(expressionManualVars+' '+self.oacc_scopeManualPtr).strip().replace(' ',',')
                self.oacc_kernelsManualPtrs.append((expressionManualVars+' '+self.oacc_scopeManualPtr).strip().replace(' ',','))
            else:
                self.oacc_kernelsManualPtrs.append('')
            #   - speculative implicit memory allocation/transfers
            self.code=self.code+self.mark_implicitcopy('in',self.oacc_kernelId)
            # * generate dummy kernel launch function call
            self.code=self.code+self.prefix_kernel+str(self.oacc_kernelId)+'();'
            self.carry_loopAttr2For(root,False,[],[],'','',[],'')
            self.oacc_kernels.append(root)
            # * generate proper code after the kernels region:
            #   - copy, copyout (transfer)
            if copyoutId!=-1: #expressionAll!='':
                self.code=self.code+('\t'*depth)+self.prefix_datacpout+str(copyoutId)+'();'
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
            self.oacc_kernelsAssociatedCopyIds.append(scope_associated_copy_ids)
        elif root.tag == 'pragma' and root.attrib.get('directive')=='algorithm':
            # case 2: algorithm
            self.code=self.code+'//got the clause: '+root.attrib.get('clause')+'\n'
            outputOfAlgorithm=self.codegen_generate_algorithm(root.attrib.get('clause'))
        elif root.tag == 'pragma' and (root.attrib.get('directive')=='enter' or root.attrib.get('directive')=='exit'):
            # case 3: 
            self.code=self.code+'//got an '+root.attrib.get('directive')+' clause: '+root.attrib.get('clause')+'\n'
            # parse data clauses and
            [expressionIn, expressionAlloc, expressionOut, expressionAll] = self.oacc_clauseparser_data(str(root.attrib.get('clause')),str(self.oacc_copyId), root.attrib.get('directive')=='enter', root.attrib.get('directive')=='exit')
            if DEBUGENTEREXIT>0:
                print expressionIn+'\n'+expressionAlloc+'\n'+expressionOut # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
                print 'all data clauses: '+expressionAll
            # dump pragma copyin allocation/transfer before region
# HERE
            copyoutId=self.util_copyIdAppend(expressionIn, expressionAlloc, expressionOut, depth, expressionAll)
            scope_associated_copy_ids+=[copyoutId]
            self.code=self.code+('\t'*depth)+self.prefix_datacpout+str(copyoutId)+'();'
# TO HERE
            #   - manual variables (explicit copies)
            #temp_scopeManual=self.varname_extractor(expressionAll)
            #if temp_scopeManual!='':
            #    self.oacc_scopeManualPtr=self.oacc_scopeManualPtr+temp_scopeManual+' '
        elif root.getchildren()==[]:
            # case 4: no descendent is found
            if root.tag == 'for':
                # for is special case, handle it specially
                self.code=self.code+str('\t'*depth)+'for('+str(root.attrib.get('initial'))+';'+str(root.attrib.get('boundary'))+';'+str(root.attrib.get('increment'))+')'
            self.code=self.code+str(root.text)
        else:
            # case 5: go through descendents recursively
            expressionIn=''
            expressionAlloc=''
            expressionOut=''
            expressionAll=''
            copyoutId=-1
            temp_scopeAutoma=''
            temp_scopeManual=''
            if root.tag == 'for':
                self.code=self.code+str('\t'*depth)+'for('+str(root.attrib.get('initial'))+';'+str(root.attrib.get('boundary'))+';'+str(root.attrib.get('increment'))+')'
            elif (root.tag=='pragma' and root.attrib.get('directive')=='data'):
                # parse data clauses and
                [expressionIn, expressionAlloc, expressionOut, expressionAll] = self.oacc_clauseparser_data(str(root.attrib.get('clause')),str(self.oacc_copyId), False, False)
                if DEBUGCP>0:
                    print expressionIn+'\n'+expressionAlloc+'\n'+expressionOut # expressionIn format: varname="a" in="true" present="true" dim0="0:SIZE"
                    print 'all data clauses: '+expressionAll
                # dump pragma copyin allocation/transfer before region
# HERE
                copyoutId=self.util_copyIdAppend(expressionIn, expressionAlloc, expressionOut, depth, expressionAll)
                scope_associated_copy_ids+=[copyoutId]
# TO HERE
                #   - automatic variables [deviceptr] (update deviceptr variable of this scope, if anything is defined)
                temp_scopeAutoma=self.oacc_clauseparser_deviceptr(str(root.attrib.get('clause')))
                if temp_scopeAutoma!='':
                    self.oacc_scopeAutomaPtr=self.oacc_scopeAutomaPtr+temp_scopeAutoma+' '
                #   - manual variables (explicit copies)
                temp_scopeManual=self.varname_extractor(expressionAll)
                if temp_scopeManual!='':
                    self.oacc_scopeManualPtr=self.oacc_scopeManualPtr+temp_scopeManual+' '
            for child in root:
                self.code_descendentRetrieve(child,depth+1,scope_associated_copy_ids)
            # dump pragma copyout transfer after the region
            if (root.tag=='pragma' and root.attrib.get('directive')=='data') and copyoutId!=-1:
                # dump pragma transfer after region
                self.code=self.code+('\t'*depth)+self.prefix_datacpout+str(copyoutId)+'();'
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
        if USEPYCPARSER:
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
        else:
            #srcML
            self.astRootML = srcml_code2xml(self.code)
            if DEBUGSRCMLC: print 'Error 1019! Unimplemented AST generator!'
            exit(-1)

    def var_kernel_parentsFind(self):
        self.var_findFuncParents("kernel")

    def var_copy_parentsFind(self):
        self.var_findFuncParents("data")
        if len(self.oacc_copysVarNams)!=self.oacc_copyId or len(self.oacc_copysVarTyps)!=self.oacc_copyId:
            print 'internal error! could not determine the parent function of data copy statement!'
            exit(-1)
    
    def var_findFuncParents(self,funcName):
        # find the parent of function
        # parent of function A is a function calling A
        # here, the parent is unique since the funcName is unique autogenerated name
        if USEPYCPARSER:
            root = self.astRoot
        else:
            # srcML
            root = self.astRootML
            if DEBUGSRCMLC: print 'Error 1040! Unimplemented AST parser!'
            #exit(-1)
        
        fname=''
        count  = self.oacc_kernelId if funcName=="kernel" else self.oacc_copyId
        prefix = self.prefix_kernel if funcName=="kernel" else self.prefix_datacpin
        for id in range(0,count):
            # go through all functions in the code (C/C++ code)
            # find the function which the function is called there
            # then find the type of all variables
            kn=prefix+str(id)
            funcVars=[]
            funcTyps=[]
            if USEPYCPARSER:
                for func in root.findall(".//FuncDef"):
                    funcFound=0
                    # print('we have found '+str(len(func.findall(".//FuncCall/ID")))+' function calls in '+str(func.find('Decl').get('uid')))
                    for fcall in func.findall(".//FuncCall/ID"):
                        if str(fcall.get('uid')).strip()==kn.strip():
                            funcFound=1
                            fname=func.find('Decl').get('uid')
                            if DEBUGFC:
                                fname=self.wrapFuncName(fname)
                                print 'function name> '+fname
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
                        
                        break
            else:
                # srcML
                [template,fname]=srcml_get_parent_fcn(root,kn.strip())
                [fnV, fnT]=srcml_get_var_details(root, fname)
                if DEBUGCPARSER>0:
                    print 'declared  vars > '+','.join(fnV)
                    print 'declared types > '+','.join(fnT)
                self.forward_declare_append_new_types(fnT)
                funcVars=fnV
                funcTyps=fnT
                if DEBUGSRCMLC: print 'Error 1093! unimplemented AST parser!'
                # get variables declared within the kernel 
                # print id, len(self.oacc_kernels[id]), funcName
                if funcName=="kernel":
                    kernel_core_body = self.scanner_xml2code(self.oacc_kernels[id])
                    [kernelLocalVN, kernelLocalVT] = srcml_get_var_details(srcml_code2xml(kernel_core_body), '')
            # make sure functionParent is found
            if fname=='':
                print 'Fatal Internal Error!'
                print 'could not find the generated function'
                print '\t'+kn.strip()+' is not called in following XML tree:'
                print tostring(root)
                exit(-1)
            fname=self.wrapFuncName(fname)
            if DEBUGFC:
                print kn.strip()+' is called in '+fname
            # At this point we have fname, funcVars, funcTypes here
            if funcName=="kernel":
                self.oacc_kernelsVarNams.append(funcVars)
                self.oacc_kernelsVarTyps.append(funcTyps)
                self.oacc_kernelsParent.append(fname)
                self.oacc_kernelsTemplates.append(template)
                self.oacc_kernelsLocalVarNams.append(kernelLocalVN)
                self.oacc_kernelsLocalVarTyps.append(kernelLocalVT)
            else:
                self.oacc_copysVarNams.append(funcVars)
                self.oacc_copysVarTyps.append(funcTyps)
                self.oacc_copysParent.append(fname) 

    # YACC-friendly code generator
    def var_parseForYacc(self, InCode):
        # here  the InCode has no comment block or comment line
        # 1) instead of removing include, we put a workout:
        code="#define __attribute__(x)\n"+"#define __asm__(x)\n"+"#define __builtin_va_list int\n"+"#define __const\n"+"#define __restrict\n"+"#define __extension__\n"+"#define __inline__\n"+InCode
        #code = InCode
        #re.sub(r'(#include).*.(\n)', '', code)
        code=self.preprocess_by_gnu_cpp(code)
        return code.strip()

    def argument_parser(self):
        args=[]
        if DEBUGCPP: print 'printing args <'+self.nvcc_args+'>'
        skip=False
        capture=False
        for arg in self.nvcc_args.split():
            if skip:
                skip=False
                continue
            if capture:
                capture=False
                args.append(arg)
            ch=arg[0:2]
            if   ch=='-D' or ch=='-I':
                args.append(arg)
                if arg=='-I': capture=True #swallow the next argument blindly
            elif ch=='-o':
                skip=True
        if DEBUGCPP: print '\targs> '+', '.join(args)
        return args


    def preprocess_by_gnu_cpp(self, codein):
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(codein)
        f.close()
        # 2) replace #define and unroll #include using GNU cpp 
        if DEBUGCPP:
            print('opening input file <'+f.name+'>')
            print('cat '+f.name+' | '+"cpp -E -I"+os.path.dirname(os.path.realpath(__file__))+"/../include/ -I"+os.path.dirname(self.foname))
            #exit(-1)
        cpp_call =["cpp", "-x", "c++", "-E", "-I"+os.path.dirname(os.path.realpath(__file__))+"/../include/", "-I"+os.path.dirname(self.foname)+"/./"]
        cpp_call+=self.argument_parser()
        if DEBUGCPP: print 'cpp call: '+', '.join(cpp_call)

        p1 = Popen(["cat", f.name], stdout=PIPE)
        #p2 = Popen(["cpp", "-x", "c++", "-E", "-I"+os.path.dirname(os.path.realpath(__file__))+"/../include/", "-I"+os.path.dirname(self.foname)+"/./"], stdin=p1.stdout, stdout=PIPE)
        p2 = Popen(cpp_call, stdin=p1.stdout, stdout=PIPE)
        code = p2.communicate()[0]
        os.remove(f.name)
        # 3) remove cpp # in the begining of file
        code=re.sub(r'(#\ ).*.(\n)', '', code)
        code=code.replace("extern \"C\"",'');
        return code

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
        # then find the size of given variable
        if USEPYCPARSER:
            for func in root.findall(".//FuncDef"):
                if self.wrapFuncName(func.find('Decl').get('uid').strip())==funcName.strip():
                    # print('inside '+funcName[cn])
                    funcBody=func.find('Compound')
                    if func.find('.//ParamList'):
                        funcBody.append(func.find('.//ParamList'))
                    for var in funcBody.findall(".//Decl"):
                        # single variable Decl
                        if var.get('uid').split(',')[0].strip()==varName.strip():
                            init='unitilialized'
                            if len(var)==2:
                                # print('declaration and initialization')
                                size = self.declareRecursive(var[0])
                                init = self.initilizieRecursive(var[1])
                            elif len(var)==1:
                                #print('only declerations')
                                size = self.declareRecursive(var[0])
                            else:
                                print('unexpected number of children')
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
        else:
            # srcML
            size=srcml_find_var_size(root, funcName, varName)
            if size.find('unkown')!=-1:
                print('Error: Unable to determine the array size ('+varName.strip()+')')
                exit(-1)
            if size.find('dynamic')!=-1:
                if DEBUGCP>1:
                    print('dynamic array detected ('+varName.strip()+')')
            if DEBUGCP>2:
                print size
            if DEBUGSRCMLC:
                print 'Error 1215! unimplemented AST parser!'
            if DEBUGSRCML:
                print 'function:'+funcName+' variable:'+varName+' size:'+size
            if size!='':
                return size
            #exit(-1)
        print('Fatal Internal Error! could not determine the size of variable:'+varName+' in the function:'+funcName+'!')
        exit(-1)

    def var_copy_showAll(self):
        # print detected copy statements to stdout
        for [id, i] in self.oacc_copys:
            print i

    def var_copy_genCode(self):
        # generate proper code for all the copy expressions
        # even generated with data, kernels, or parallel directive
        # and relpace dummy data copy functions with proper allocation and data tansfers

        regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:/\+\^\|\&\(\)\*\ \[\]\.><-]*)(\")')
        # explicit memory copies
        for i in range(0,len(self.oacc_copys)):
            codeCin='' #code for performing copyin
            codeCout='' #code for performing copyin
            codeM='' #code for performing allocation
            vardeclare=''
            [kernel_id, d_copydetails]=self.oacc_copys[i]
            #for j in cp_expression.split('\n'):
            for j in d_copydetails: #.split('\n'):
                varname=j['varname']#''
                incom=j['in']       #''
                present=j['present']#'false'
                dim=[]
                for d in [0, 1, 2, 3]:
                    try:
                        dim.append(j['dim'+str(d)])
                    except:
                        break
                type=j['type']
                dname=j['dname']
                size=j['size']
                parentFunc=j['parentFunc']
                clause=j['clause']
                dataid=j['dataid']
                pseudotp=j['pseudotp'] if 'pseudotp' in j else ''
                isexit=True if j['isenterdirective']=='true' else False
                isenter=True if j['isexitdirective']=='true' else False
                compression=j['compression']
                min=j['min'] if 'min' in j else ''
                max=j['max'] if 'max' in j else ''
                # if DEBUGCP>1:
                #     print 'Copy tuple > '+j
                # for (a, b, c, d, e) in regex.findall(j):
                #     if DEBUGREGEX:
                #         print j+'> '+','.join([a,b,c,d,e])
                #     if a=='varname':
                #         varname=d
                #     elif a=='in':
                #         incom=d
                #     elif a=='present':
                #         present=d
                #     elif a.find('dim')!=-1:
                #         dim.append(d)
                #     elif a=='type':
                #         type=d
                #     elif a=='dname':
                #         dname=d
                #     elif a=='size':
                #         size=d
                #     elif a=='parentFunc':
                #         parentFunc=d
                #     elif a=='clause':
                #         clause=d
                #     elif a=='dataid':
                #         dataid=d
                #     elif a=='pseudotp':
                #         pseudotp=d
                #     elif a=='isenterdirective':
                #         isenter= True if d=='true' else False
                #     elif a=='isexitdirective':
                #         isexit= True if d=='true' else False
                #     elif a=='compression':
                #         compression=d
                #     elif a=='max':
                #         max=d
                #     elif a=='min':
                #         min=d
                # handle dynamic allocation here
                if size.find('dynamic')!=-1 and clause!='present':
                    if size.count('dynamic')!=len(dim) and not self.oacc_data_dynamicAllowed(clause):
                        print 'Error: [data clause] unable to find a match for variable size! variable name: '+varname+' - clause('+clause+')'
                        exit(-1)
                    for repa in dim:
                        if repa.find(':')==-1:
                            print 'Error: dynamic array without the length at the data clause!'
                            print '\tvariable name: '+varname
                            print '\trange statement: '+repa
                            print '\tsize: '+size
                            print '\tclause: '+clause
                            exit(-1)
                        size=size.replace('dynamic',repa.split(':')[1]+'+'+repa.split(':')[0])
                # duplication check for declaration and allocation
                varmapper_allocated_found=False
                for (pp1, pp2, pp3) in self.varmapper_allocated:
                    if pp1==parentFunc and pp2==dname and pp3==dataid:
                        varmapper_allocated_found=True
                        break
                scalar_copy=(type.count('*')==0) and pseudotp==''
                ispresent=self.oacc_clauseparser_data_ispresent(clause)
                if varmapper_allocated_found==False and not isexit: # no allocation is needed for those coming from 'pragma exit'
                    # generate declaration
                    # TODO vardeclare+=self.codegen_devPtrDeclare(type,dname,scalar_copy)+'/* '+dataid+' */\n'
                    # generate accelerator allocation
                    if present=='true':
                        codeM+=self.codegen_accDevicePtr(dname,size,varname,type,scalar_copy)
                        codeM+='if('+dname+'==NULL){\n'
                        codeM=codeM+'ipmacc_prompt((char*)"IPMACC: memory allocation '+varname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size,varname,type,scalar_copy, ispresent, pseudotp, compression, min, max)
                        codeM+='}\n'
                        print 'unexpected reach! '
                        exit(-1)
                    elif clause!='present':
                        codeM=codeM+'ipmacc_prompt((char*)"IPMACC: memory allocation '+varname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size,varname,type,scalar_copy, ispresent, pseudotp, compression, min, max)
                    self.varmapper_allocated.append((parentFunc,dname,dataid))
                # generate memory copy code
                if clause=='copyin' or clause=='copy':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: memory copyin '+varname+'\\n");\n'
                    #codeC+=self.codegen_memCpy(dname, ('&' if scalar_copy else '')+varname, size, 'in')
                    codeCin+=self.codegen_accCopyin(('&' if scalar_copy else '')+varname, dname, size, type, '', scalar_copy, pseudotp)
                if clause=='ccopyin' or clause=='compression_copyin' or clause=='ccopy' or clause=='compression_copy':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: compression and memory copyin '+varname+'\\n");\n'
                    codeCin+=self.codegen_accCompCopyin(('&' if scalar_copy else '')+varname, dname, size, type, '', scalar_copy,parentFunc,min,max)
                if clause=='pcopyin' or clause=='pcopy' or clause=='present_or_copyin' or clause=='present_or_copy':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: memory copyin '+varname+'\\n");\n'
                    codeCin+=self.codegen_accCopyin(('&' if scalar_copy else '')+varname, dname, size, type, 'p', scalar_copy, pseudotp)
                if clause=='pccopyin' or clause=='pccopy' or clause=='present_or_compression_copyin' or clause=='present_or_compression_copy':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: compression and memory copyin '+varname+'\\n");\n'
                    codeCin+=self.codegen_accCompCopyin(('&' if scalar_copy else '')+varname, dname, size, type, 'p', scalar_copy,parentFunc,min,max)
                #if clause=='present_or_create':
                #    codeCin+='ipmacc_prompt("IPMACC: memory create or getting device pointer for '+varname+'\\n");\n'
                #    codeCin+=self.codegen_memAlloc(('&' if scalar_copy else '')+varname, dname, size, type)
                if clause=='present':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: memory getting device pointer for '+varname+'\\n");\n'
                    codeCin+=self.codegen_accPresent(('&' if scalar_copy else '')+varname, dname, size, type)
                if clause=='copyout' or clause=='copy' or clause=='pcopyout' or clause=='pcopy' or clause=='present_or_copyout':
                    codeCout+='ipmacc_prompt((char*)"IPMACC: memory copyout '+varname+'\\n");\n'
                    #codeC+=self.codegen_memCpy(('&' if scalar_copy else '')+varname, dname, size, 'out')
                    #codeM+=self.codegen_memAlloc(dname,size,varname,type,scalar_copy, ispresent)
                    codeCout+=self.codegen_accPCopyout(('&' if scalar_copy else '')+varname, dname, size, type, scalar_copy, pseudotp)
                if clause=='ccopy' or clause=='compression_copy' or clause=='pccopy' or clause=='present_or_copression_copy':
                    codeCout+='ipmacc_prompt((char*)"IPMACC: memory copyout and decompression '+varname+'\\n");\n'
                    #codeC+=self.codegen_memCpy(('&' if scalar_copy else '')+varname, dname, size, 'out')
                    #codeM+=self.codegen_memAlloc(dname,size,varname,type,scalar_copy, ispresent)
                    codeCout+=self.codegen_accPCompCopyout(('&' if scalar_copy else '')+varname, dname, size, type, scalar_copy,parentFunc)
            #self.code_include=self.code_include+vardeclare
            self.code=self.code.replace(self.prefix_dataalloc+str(i)+'();',vardeclare+codeM)
            profiling_in = ''
            profiling_out= ''
            if PROFILER and codeCin!='':
                profiling_in  ='acc_profiler_start();\n'
                profiling_out ='acc_profiler_end(2);\n'
            self.code=self.code.replace(self.prefix_datacpin+str(i)+'();',profiling_in+codeCin+profiling_out)
            profiling_in = ''
            profiling_out= ''
            if PROFILER and codeCout!='':
                profiling_in  ='acc_profiler_start();\n'
                profiling_out ='acc_profiler_end(2);\n'
            self.code=self.code.replace(self.prefix_datacpout+str(i)+'();',profiling_in+codeCout+profiling_out)

        # implicit/reduction memory copies
        for i in range(0,len(self.oacc_kernelsImplicit)):
            codeCin='' #code for performing copy in
            codeCout='' #code for performing copy in
            codeM='' #code for performing allocation
            vardeclare=''
            if len(self.oacc_kernelsReductions)!=len(self.oacc_kernelsImplicit):
                print 'Fatal internal error!\n'
                print 'There should be equal instances of kernelsImplicit and kernelsReduction, one per kernels region'
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
                griddimen=''
                dataid=str(i)
                pseudotp=''
                compression=''
#                regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*\ ]*)(\")')
                for (a, b, c, d, e) in regex.findall(j):
                    if a=='varname':
                        varname=d
                    elif a=='present':
                        present=d
                    elif a=='gridDim':
                        griddimen=d
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
                    elif a=='pseudotp':
                        pseudotp=d
                    elif a=='compression':
                        compression=d
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
                            print '\tsize: '+size
                            exit(-1)
                        size=size.replace('dynamic',repa.split(':')[1]+'+'+repa.split(':')[0])
                # duplication check for declaration and allocation
                varmapper_allocated_found=False
                dIDs=[]
                dIDs+=self.oacc_kernelsAssociatedCopyIds[i]
                dIDs.reverse()
                for (pp1, pp2, pp3) in self.varmapper_allocated:
                    for did in dIDs:
                        if pp1==parentFunc and pp2==dname and pp3==did:
                            varmapper_allocated_found=True
                            dataid=did
                            break
                    if varmapper_allocated_found:
                        break
                scalar_copy=(type.count('*')==0 and pseudotp.count('*')==0)
                if varmapper_allocated_found==False:
                    # generate declaration
                    # TODO vardeclare+=self.codegen_devPtrDeclare(type,dname,scalar_copy)+'/* '+dataid+'*/\n'
                    #vardeclare+='short '+dname+self.suffix_present+'='+('0')+';\n' # for now we assume are variables are present
                    # generate accelerator allocation
                    if present=='true':
                        # this lines
                        # codeM+='if(!'+dname+self.suffix_present+'){\n'
                        # codeM+=dname+self.suffix_present+'++;\n'
                        # are replaced with following two lines #FIXME
                        #codeM+=dname+'=('+type+')acc_deviceptr((void*)'+('&'if scalar_copy else '')+varname+');\n'
                        codeM+=self.codegen_accDevicePtr(dname,size,varname,type,scalar_copy)
                        codeM+='if('+dname+'==NULL){\n'
                        codeM=codeM+'ipmacc_prompt((char*)"IPMACC: memory allocation '+varname+'\\n");\n'
                        codeM+=self.codegen_memAlloc(dname,size,varname,type,scalar_copy, False, pseudotp)
                        codeM+='}\n'
                        print 'Unexpected reachment!'
                        exit(-1)
#                    else:
                    self.varmapper_allocated.append((parentFunc,dname,dataid))

                # this line is removed codeM+='if(!'+dname+self.suffix_present+'){\n'
                codeM=codeM+'ipmacc_prompt((char*)"IPMACC: memory allocation '+varname+'\\n");\n'
                #codeM+= self.codegen_memAlloc(dname,size,varname,type,scalar_copy, False)
                if reduc!='':
                    if REDUCTION_TWOLEVELTREE:
                        arrname  = self.prefix_kernel_reduction_array+varname
                        codeM+= type+' '+arrname+'=NULL;\n'
                        #codeM+= 'static '+type+' '+arrname+'=NULL;\n'
                        codeM+= 'if('+arrname+'==NULL){\n'
                        codeM+= arrname+'=('+type+')malloc('+size+');\n'
                        codeM+= self.codegen_memAlloc(dname,size,arrname,type,scalar_copy, False, pseudotp, compression, min, max)

                        codeM+= 'for(int __ipmacc_initialize_rv=0; __ipmacc_initialize_rv<'+griddimen+'; __ipmacc_initialize_rv++){\n'
                        if reduc=='min':
                            codeM+=arrname+'[__ipmacc_initialize_rv]= INT_MIN;\n'
                        elif reduc=='max':
                            codeM+=arrname+'[__ipmacc_initialize_rv]= INT_MAX;\n'
                        elif (reduc=='&' or reduc=='&&'):
                            codeM+=arrname+'[__ipmacc_initialize_rv]= 1;\n'
                        else:
                            codeM+=arrname+'[__ipmacc_initialize_rv]= 0;\n'
                        codeM+= '}\n'
                        codeM+= self.codegen_accCopyin(arrname, dname, size, type, 'p',scalar_copy, pseudotp)

                        codeM+= '}\n'
                    else:
                        codeM+= self.codegen_memAlloc(dname,size,varname,type,scalar_copy, False, pseudotp, compression, min, max)
                # this line is removed codeM=codeM+'}\n'

                # generate memory copy in/out code
                passbyref='' if reduc=='' and (not scalar_copy) else '&'
#                if incom=='true':
                if reduc=='':
                    codeCin+='ipmacc_prompt((char*)"IPMACC: memory copyin '+varname+'\\n");\n'
                    #codeCin+=self.codegen_memCpy(dname, passbyref+varname, size, 'in')
                    codeCin+=self.codegen_accCopyin(passbyref+varname, dname, size, type, 'p', scalar_copy, pseudotp)
                    codeCout+='ipmacc_prompt((char*)"IPMACC: memory copyout '+varname+'\\n");\n'
                    #codeCout+=self.codegen_memCpy(passbyref+varname, dname, size, 'out')
                    codeCout+=self.codegen_accPCopyout(passbyref+varname, dname, size, type, scalar_copy, pseudotp)
                else:
                    if REDUCTION_TWOLEVELTREE:
                        ## allocate host memory
                        #arrname=self.prefix_kernel_reduction_array+varname
                        #codeCin += type+' '+self.prefix_kernel_reduction_array+varname+'=NULL;\n'
                        #codeCin += arrname+'=('+type+')malloc('+size+');\n'
                        codeCout+='ipmacc_prompt((char*)"IPMACC: memory copyout '+varname+'\\n");\n'
                        #codeCout+=self.codegen_memCpy(arrname, dname, size, 'out')
                        codeCout+=self.codegen_accPCopyout(arrname, dname, size, type, scalar_copy, pseudotp)
                        iterator =self.prefix_kernel_reduction_iterator
                        codeCout+='\n/* second-level reduction on '+varname+' */\n'
                        codeCout+='{\n'
                        codeCout+='int '+iterator+'=0;\n'
                        codeCout+='{\n'
                        codeCout+='int bound = '+griddimen+'-1;\n'
                        codeCout+='if(getenv("IPMACC_VERBOSE")) printf("IPMACC: host-side reduction size: %d\\n",'+griddimen+');\n'
                        #codeCout+='int bound = ('++')==0?('+griddimen+'-2):('+griddimen+'-1);\n'
                        codeCout+='for('+iterator+'=bound; '+ iterator+'>0; '+iterator+'-=1){\n'
                        des=arrname+'['+iterator+'-1]'
                        src=arrname+'['+iterator+']'
                        if reduc=='min':
                            codeCout+=des+'=('+(des+'>'+src)+'?'+(src)+':'+(des)+');\n'
                        elif reduc=='max':
                            codeCout+=des+'=('+(des+'>'+src)+'?'+(des)+':'+(src)+');\n'
                        else:
                            codeCout+=des+'='+des+reduc+src+';\n'
                        codeCout+='}\n'
                        codeCout+='}\n'
                        codeCout+='}\n'
                        codeCout+=varname+'='+arrname+'[0];\n'
                        codeCout+='free('+arrname+');\n'

                    else:
                        codeCin +='ipmacc_prompt((char*)"IPMACC: memory copyin '+varname+'\\n");\n'
                        #codeCin +=self.codegen_memCpy(dname, passbyref+varname, size, 'in')
                        codeCin +=self.codegen_accCopyin(passbyref+varname, dname, size, type, 'p', scalar_copy, pseudotp)
                        codeCout+='ipmacc_prompt((char*)"IPMACC: memory copyout '+varname+'\\n");\n'
                        #codeCout+=self.codegen_memCpy(passbyref+varname, dname, size, 'out')
                        codeCout+=self.codegen_accPCopyout(passbyref+varname, dname, size, type, scalar_copy, pseudotp)
                    # reduction do not need copy in for two-level tree
            #self.code_include=self.code_include+vardeclare
            #self.code=self.code.replace(self.prefix_dataalloc+str(i)+'();',vardeclare+codeM)
            profiling_in = ''
            profiling_out= ''
            if PROFILER and codeM!='':
                profiling_in  ='acc_profiler_start();\n'
                profiling_out ='acc_profiler_end(2);\n'
            self.code=self.code.replace(self.prefix_dataimpli+'in'+str(i)+'();',vardeclare+codeM+profiling_in+codeCin+profiling_out)
            profiling_in = ''
            profiling_out= ''
            if PROFILER and codeCout!='':
                profiling_in  ='acc_profiler_start();\n'
                profiling_out ='acc_profiler_end(2);\n'
            self.code=self.code.replace(self.prefix_dataimpli+'out'+str(i)+'();',profiling_in+codeCout+profiling_out)
   
    
    def var_copy_assignExpDetail(self, forDimOfAllKernels, blockDim):
        # find the type, size, and parentFunction of variables referred in each copy expression
        # and append it to the existing expression

        if USEPYCPARSER:
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
        else:
            #srcML
            root=srcml_code2xml(self.code)
            if DEBUGSRCMLC: print 'Error 1498! Unimplemented AST generator!'
            #exit(-1)
             
        # explicit memory copies
        for i in range(0,len(self.oacc_copys)):
            #print i
            [kernel_id, l_d_cp_expression]=self.oacc_copys[i]
            #list=(cp_expression).split('\n')
            d_copydetails = [{}]*(len(l_d_cp_expression)-1)
            self.oacc_copys[i]=''
            #for j in range(0,len(list)-1):
            # print l_d_cp_expression
            for j in range(0,len(l_d_cp_expression)-1):
                #regex = re.compile(r'([a-zA-Z0-9_]*)([=])(\")([a-zA-Z0-9_:\(\)\*]*)(\")')
                #if DEBUGREGEX:
                #    print 'regex='+str(regex.findall(list[j]))
                #for (a, b, c, d, e) in regex.findall(list[j]):
                d_tmp = {}
                for a, d in l_d_cp_expression[j].iteritems():
                    d_tmp[a] = d
                    if a=='varname':
                        # find the `d` variable in the region
                        try:
                            varNameList=self.oacc_copysVarNams[i]
                            varTypeList=self.oacc_copysVarTyps[i]
                            #print varTypeList[varNameList.index(d)]
                            foundType=varTypeList[varNameList.index(d)]
                            if self.container_class_supported(foundType):
                                #list[j]=list[j]+' type="'+foundType+'" pseudotp="'+self.container_class_pseudo(foundType)+'"'
                                # list[j]=list[j]+' type="'+foundType+'" pseudotp="'+self.container_class_pseudo(foundType)+'"'
                                d_tmp['type'] = foundType
                                d_tmp['pseudotp'] = self.container_class_pseudo(foundType)
                            else:
                                # list[j]=list[j]+' type="'+foundType+'"'
                                d_tmp['type'] = foundType
                        except:
                            print "fatal error! variable "+d+" is undefined!"
                            print str(len(self.oacc_copysVarNams))+' '+str(len(self.oacc_copys))
                            print "defined  vars: "+','.join(varNameList)
                            print "defined types: "+','.join(varTypeList)
                            exit(-1)
                        # list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_copysParent[i],d,[i])+'"'
                        # list[j]=list[j]+' size="'+self.var_find_size(d,self.oacc_copysParent[i],root)+'"'
                        # list[j]=list[j]+' parentFunc="'+self.oacc_copysParent[i]+'"'
                        d_tmp['dname'] = self.varmapper_getDeviceName_elseCreate(self.oacc_copysParent[i],d,[i])
                        d_tmp['size'] = self.var_find_size(d,self.oacc_copysParent[i],root)
                        d_tmp['parentFunc'] = self.oacc_copysParent[i]
                d_copydetails[j] = d_tmp
            if DEBUGCP>0:
                # print '\n'.join(list[0:len(list)-1])
                print d_copydetails
            self.oacc_copys[i]=[kernel_id, d_copydetails]
            #self.oacc_copys[i]=[kernel_id, '\n'.join(list[0:len(list)-1])]

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
                    print "fatal error! implicit variable "+d+" is undefined!"
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
                [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(i)
                if (nctadim>1 or GENMULTIDIMTB) and len(list)>0:
                    #kernelGridDim='(('+'*'.join(forDimOfAllKernels[i])+')/('+'*'.join([ctadimx,ctadimy,ctadimz])+')+1)'
                    kernelGridDim ='(('+forDimOfAllKernels[i][0]+')/('+ctadimx+')+1)'
                    kernelGridDim+='*(('+forDimOfAllKernels[i][1]+')/('+ctadimy+')+1)'
                    if nctadim>2: kernelGridDim+='*(('+forDimOfAllKernels[i][2]+')/('+ctadimz+')+1)'
                    kernelGridDim='('+kernelGridDim+')'
                    #print 'kernelGridDim> '+kernelGridDim
                    #print 'error: reduction is not tested under multi-dimensional grid. Disable GENMULTIDIMTB in codegen.py'
                    #exit(-1)
                else:
                    kernelGridDim='('+forDimOfAllKernels[i]+'/'+blockDim+'+1)'
                [vnm, init, op, asi, tp, depth]=list[j]
                if vnm.strip()=='':
                    list[j]=''
                    continue
                list[j]='varname="'+vnm+'"'
                list[j]+=' initia="'+init+'"'
                list[j]+=' operat="'+op+'"'
                list[j]+=' redoverdepth="'+depth+'"'
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
                    print "fatal error! reduction variable "+vnm+" is undefined!"
                    exit(-1)
                list[j]=list[j]+' dname="'+self.varmapper_getDeviceName_elseCreate(self.oacc_kernelsParent[i],vnm,self.oacc_kernelsAssociatedCopyIds[i])+'"'
                list[j]=list[j]+' size="'+((kernelGridDim+'*') if REDUCTION_TWOLEVELTREE else '')+self.var_find_size(vnm,self.oacc_kernelsParent[i],root)+'"'
                list[j]=list[j]+' gridDim="'+kernelGridDim+'"'
                list[j]=list[j]+' parentFunc="'+self.oacc_kernelsParent[i]+'"'
            if DEBUGPRIVRED:
                print 'reduction copies for kernel'+str(i)+'> '+('\n'.join(list))
            self.oacc_kernelsReductions[i]='\n'.join(list)

    # varmapper fuctions
    # handle the mapping between host and device variables
    def varmapper_getDeviceName_elseCreate(self,function,varname, dIDsI=[]):
        # return the deviceName of varname. if does not exist, create one.
        dIDs=dIDsI
        dIDs.reverse()
        for dID in dIDs+[-1]:
            for (a, b, c, d) in self.varmapper:
                if a==function and b==varname and (dID==-1 or dID==c):
                    return d
        dID = -1 if len(dIDs)==0 else dIDs[0]
        dvarname=self.prefix_varmapper+function+'_'+varname+('_'+str(dID) if dID!=-1 else '')
        self.varmapper.append((function, varname, dID, dvarname))
        return dvarname

    def varmapper_getDeviceName(self,function,varname,dIDsI=[]):
        # return the deviceName of varname. if does not exist, create one.
        dIDs=dIDsI
        dIDs.reverse()
        for dID in dIDs+[-1]:
            for (a, b, c, d) in self.varmapper:
                if a==function and b==varname and (dID==-1 or dID==c):
                    return d
        return varname
       
    def varmapper_showAll(self):
        # show all (function, hostVariable) -> deviceVariable mappings
        for (a, b, c, d) in self.varmapper:
            print '('+a+','+b+'.'+c+')->'+d


    def pycparser_getAstTree(self,code):
        text=self.code
        text=text+'int __ipmacc_main(){\n'+code+';\n}'
        text=self.var_parseForYacc(text)
        if DEBUGCPARSER:
            print text
        # handle the error
        if ERRORDUMP:
            f = open('./__ipmacc_c_code_unable_to_parse.c','w')
            old_stdout = sys.stdout
            sys.stdout = f
            print text
            sys.stdout = old_stdout
            f.close()
            sys.stdout = old_stdout
        # create a pycparser
        parser = c_parser.CParser()
        ast = parser.parse(text, filename='<none>')
        if ERRORDUMP:
            os.remove('__ipmacc_c_code_unable_to_parse.c')
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
        if USEPYCPARSER:
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
        else:
            #srcML
            self.astRootML = srcml_code2xml(self.code)
            if DEBUGSRCMLC:
                #print self.astRootML
                print 'Error 1719! Unimplemented AST generator!'
            #exit(-1)

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
        #regex = re.compile(r'([A-Za-z0-9]+)([\ ]*)(\((.+?)\))*')
        indep=False
        private=[]
        reduction=[]
        gang=''
        vector=''
        smc=[]
        perforation=''
        #for it in regex.findall(clause):
        for [i0, i3] in clauseDecomposer_break(clause):
            if DEBUGLD:
                print 'clause entry> '+'<>'.join([i0,i3]).strip()
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
            # gang
            elif i0.strip()=='gang' and i3.strip()!='':
                gang=i3.strip()
            # vector
            elif i0.strip()=='vector' and i3.strip()!='':
                vector=i3.strip()
            # smc
            elif i0.strip()=='smc' and i3.strip()!='':
                smc.append(i3.strip())
            # perforation
            elif i0.strip()=='perforation' and i3.strip()!='':
                perforation=i3.strip()
        if DEBUGLD:
            print 'returning> '+str(indep)+'<>'+','.join(private)+'<>'+','.join(reduction)+'<>'+gang+'<>'+vector+'<>'+perforation
        return [indep, private, reduction, gang, vector, smc, perforation]

    def code_gen_reversiFor(self, initial, boundary, increment):
        return 'for('+initial+';'+str(boundary)+';'+str(increment)+')'

    def count_loopIter(self, init, final, operator, steps, boundary):
        # initial value of operator
        # final value of operator (in respect to loop condition)
        # operator: the operator of loop iterator increment
        # steps: value of steps for each loop iterator increment
        # boundary is the for condition
        # final is the for termination value
        if boundary.find('<=')!=-1 or boundary.find('>=')!=-1:
            extraIter='+1'
        else:
            extraIter='+0'
        if operator=='*' or operator=='/':
            return 'log(abs((int)'+final+'-('+init+extraIter+'))'+')'+'/log('+steps+')'
        elif operator=='+' or operator=='-':
            return '(abs((int)'+final+'-('+init+extraIter+'))'+')'+'/(float)('+steps+')'
        else:
            print 'unexpected loop increment operator'
            exit(-1)

    def perform_implicit_copy(self, kernelId, scopeVarsNames, scopeVarsTypes, implicitCopies):
        code_copyin=''
        code_copyout=''
        if DEBUGCP>1:
            print 'Impilict Copy Checking for implicit copy'
        for var in implicitCopies:
            idx=scopeVarsNames.index(var)
            if DEBUGCP>1:
                print '\tretriving information of variable `'+var+'` ('+scopeVarsTypes[idx]+') for implicit copy'

    def oacc_get_pointer_range(self, kid, variable):
        dim_ranges = {}
        for [s_k, l_d_cpexpr] in self.oacc_copys:
            if s_k==kid:
                for l in l_d_cpexpr:
                    for key, val in l.iteritems():
                        if key.find('dim')!=-1:
                            dim_ranges[key] = val
        return dim_ranges

    def oacc_smc_find_rw_type(self, variable, vcode):
        is_written = srcml_is_written(srcml_code2xml(vcode),variable)
        if is_written:
            return 'FETCH_CHANNEL'
        else:
            return 'FETCH_CHANNEL' #'READ_ONLY'

    def oacc_smc_getVarNames(self, kernelId):
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        listOfSmc = self.oacc_loopSMC
        endList=[]
        corr=0
        if DEBUGCACHE:
            print 'List of SMC is: '+str(listOfSmc)
            #exit(-1)
        for [kid, vlist, vcode] in listOfSmc:
            # each pair corresponds to a call which will be replaced with proper SMC localization
            if kid==kernelId:
                for vop in vlist.split(','):
                    vop=vop.replace(' ','').strip()
                    if DEBUGCACHE:
                        print 'vop: '+vop
                    # find the varname, initvalue,
                    if vop.count(':')==1:
                        # valid cache notation, subarray[start:length]
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        diminfo = self.oacc_get_pointer_range(kid, variable)
                        if len(diminfo)!=1:
                            print 'error: expected one dimensional array to be cache found otherwise.'
                            print diminfo
                            print 'subarray name: ', variable
                            exit(-1)
                        else:
                            dimlow  = diminfo['dim0'].split(':')[0]
                            dimhigh = diminfo['dim0'].split(':')[1]
                        smctype = self.oacc_smc_find_rw_type(variable, vcode)
                        pivot   = spl[0].split('[')[1]
                        dwrange = '0'
                        uprange = spl[1].split(']')[0]
                        diverge = 'false' if CACHE_IMPL_MATHOD==CACHE_IMPL_MATHOD_RBI else 'true' # default to RBI, set true for RBC
                        # print variable, diminfo, dimlow, dimhigh
                        # print smctype, pivot, dwrange, uprange, diverge
                        # print self.oacc_copys
                        # exit(-1)
                        dim2low =''
                        dim2high=''
                        pivot2  =''
                        dw2range=''
                        up2range=''
                        w_dwrange = ''
                        w_uprange = ''
                        w_dw2range = ''
                        w_up2range = ''
                    elif vop.count(':')==2:
                        # valid cache notation, subarray[start:length]
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        diminfo = self.oacc_get_pointer_range(kid, variable)
                        if len(diminfo)!=2:
                            if len(diminfo)==1 and diminfo['dim0'].find('*')!=-1:
                                # assume it is flattened 2d 
                                dimlow   = diminfo['dim0'].split(':')[0]
                                dim2low  = diminfo['dim0'].split(':')[0]
                                dimhigh  = diminfo['dim0'].split(':')[1].split('*')[0]
                                dim2high = diminfo['dim0'].split(':')[1].split('*')[1]
                                print '  warning: assuming '+variable+' is flattened 2D:', dimhigh, 'by', dim2high
                            else:
                                print 'error: expected two dimensional array to be cache found otherwise.'
                                print diminfo
                                print 'subarray name: ', variable
                                exit(-1)
                        else:
                            dimlow  = diminfo['dim0'].split(':')[0]
                            dimhigh = diminfo['dim0'].split(':')[1]
                            dim2low = diminfo['dim1'].split(':')[0]
                            dim2high= diminfo['dim1'].split(':')[1]
                        #print variable, diminfo, dimlow, dimhigh
                        #print self.oacc_copys
                        smctype = self.oacc_smc_find_rw_type(variable, vcode)
                        pivot   = spl[0].split('[')[1]
                        dwrange = '0' 
                        uprange = spl[1].split(']')[0].strip()
                        try:
                            uprange = str(eval(uprange+'-1'))
                        except:
                            print uprange, 'is not constant in', vop
                            print 'aborting()'
                            exit(1)
                        diverge = 'false' if CACHE_IMPL_MATHOD==CACHE_IMPL_MATHOD_RBI else 'true' # default to RBI, set true for RBC
                        pivot2  = spl[1].split('[')[1]
                        dw2range= '0'
                        up2range= spl[2].split(']')[0].strip()
                        try:
                            up2range= str(eval(up2range+'-1'))
                        except:
                            print up2range, 'is not constant in', vop
                            print 'aborting()'
                            exit(1)
                        # print smctype, pivot, dwrange, uprange, diverge, pivot2, dw2range, up2range
                        # print '2D cache is not implemented!'
                        # print 'aborting()'
                        # exit(-1)
                        w_dwrange = ''
                        w_uprange = ''
                        w_dw2range = ''
                        w_up2range = ''
                    elif vop.count(':')==6:
                        # valid smc
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        dimlow  =spl[0].split('[')[1]
                        dimhigh =spl[1]
                        smctype =spl[2]
                        pivot   =spl[3]
                        dwrange =spl[4]
                        uprange =spl[5]
                        diverge =spl[6].split(']')[0]
                        dim2low =''
                        dim2high=''
                        pivot2  =''
                        dw2range=''
                        up2range=''
                        w_dwrange = ''
                        w_uprange = ''
                        w_dw2range = ''
                        w_up2range = ''
                    elif vop.count(':')==8:
                        # valid smc
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        dimlow  =spl[0].split('[')[1]
                        dimhigh =spl[1]
                        smctype =spl[2]
                        pivot   =spl[3]
                        dwrange =spl[4]
                        uprange =spl[5]
                        diverge =spl[6]
                        w_dwrange = spl[7]
                        w_uprange = spl[8].split(']')[0]
                        dim2low =''
                        dim2high=''
                        pivot2  =''
                        dw2range=''
                        up2range=''
                        w_dw2range = ''
                        w_up2range = ''
                    elif vop.count(':')==15:
                        # valid smc
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        dimlow  =spl[0].split('[')[1]
                        dimhigh =spl[1]
                        dim2low =spl[2]
                        dim2high=spl[3]
                        smctype =spl[4]
                        pivot   =spl[5]
                        dwrange =spl[6]
                        uprange =spl[7]
                        pivot2  =spl[8]
                        dw2range=spl[9]
                        up2range=spl[10]
                        diverge =spl[11]
                        w_dwrange = spl[12]
                        w_uprange = spl[13]
                        w_dw2range = spl[14]
                        w_up2range = spl[15].split(']')[0]
                    elif vop.count(':')==4:
                        # valid cache-style
                        print 'cache is not fully implemented! use smc instead.\n'
                        exit(-1)
                        spl=vop.split(':')
                        variable=spl[0].split('[')[0]
                        dimlow  =spl[0].split('[')[1]
                        dimhigh =spl[1]
                        smctype ='READ_ONLY'
                        pivot   ='((('+uprange+')-('+dwrange+'))/2)'
                        dwrange =spl[2]
                        uprange =spl[3]
                        diverge =spl[4].split(']')[0]
                        w_dwrange = ''
                        w_uprange = ''
                        dim2low =''
                        dim2high=''
                        pivot2  =''
                        dw2range=''
                        up2range=''
                        w_dw2range = ''
                        w_up2range = ''
                    else: # vop.count(':')!=6 or vop.count(':')!=2:
                        # invalid syntax
                        print 'invalid smc syntax: '+vop
                        print '\t usage: smc(varname[dim1-low:dim1-high:type:pivot:down-range:up-range:divergent])'
                        print '\t note: currently, only one dimension arrays are supported'
                        exit(-1)

                    # find the type
                    try :
                        idx=scopeVarsNames.index(variable)
                        type=scopeVarsTypes[idx]
                    except:
                        print 'Error: Could not determine the type of variable declared for smc: '+variable
                        exit(-1)
                    endList.append([variable, type, smctype, pivot, dwrange, uprange, diverge, corr, dimlow, dimhigh, w_dwrange, w_uprange, dim2low, dim2high, pivot2, dw2range, up2range, w_dw2range, w_up2range, vcode])
                    #endList.append([variable, type, smctype, pivot, dwrange, uprange, diverge, kid, dimlow, dimhigh])
            corr+=1
        return endList
    def get_neutralValueForOperation(self, operation):
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
        return initValu
    def oacc_privred_getVarNames(self, kernelId, listOfPrivorRed):
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        endList=[]
        corr=0
        for [kid, vlist] in listOfPrivorRed:
        #for [kid, vlist] in self.oacc_loopReductions:
            # each pair corresponds to a call which will be replaced with proper privatization or reduction
            depth=0
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
                        depth=vlist.split(':')[-1]
                        initValu=self.get_neutralValueForOperation(operation)
                    # find the type
                    try :
                        idx=scopeVarsNames.index(variable)
                        type=scopeVarsTypes[idx]
                    except:
                        print 'Error: Could not determine the type of variable declared as private/reduction: '+variable
                        exit(-1)
                    endList.append([variable, initValu, operation, corr, type, depth])
            corr+=1
        return endList

    def inflate_kernels_for_global_vars(self, kernelDeclsBody, kernelArguments):
        # append global variables to implicit copies
        # append global variables to kernels' arguments
        if len(kernelDeclsBody)!=self.oacc_kernelId:
            print 'fatal error!'
            exit(-1)
        for i in range(0,self.oacc_kernelId):
            for [tmp_fname, tmp_prototype, tmp_declbody, tmp_rettype, tmp_qualifiers, tmp_params, tmp_local_vars, tmp_scope_vars, tmp_fcalls, tmp_ids, tmp_ex_params] in self.active_calls_decl:
                #b = r'(\s|^|$)'
                res = re.findall('\\b' + tmp_fname + '\\b', kernelDeclsBody[i])
                if len(res)>0:
                    #print 'added'
                    #print tmp_ex_params
                    [tmp_ex_params_t, tmp_ex_params_v, tmp_ex_params_s] = tmp_ex_params
                    self.oacc_kernelsImplicit[i] += tmp_ex_params_v
                    #print kernelArguments[i]
                    for idx_new in range(0,len(tmp_ex_params_v)):
                        found = False
                        for idx_exi in range(0,len(kernelArguments[i])):
                            clean_ker_arg = kernelArguments[i][idx_exi].replace('__ipmacc_opt_readonlycache','')
                            if len(re.findall('\\b' + tmp_ex_params_v[idx_new] + '\\b', clean_ker_arg))>0:
                                found = True
                                break
                        if not found:
                            # append arg 
                            if DEBUGDETAILPROC: print 'didn\'t find '+tmp_ex_params_v[idx_new]+' in '+','.join(kernelArguments[i])
                            kernelArguments[i].append(tmp_ex_params_t[idx_new]+' '+tmp_ex_params_v[idx_new])
                #else:
                    #print 'couldn\'t find <'+tmp_fname+'> in <'+kernelDeclsBody[i]+'>'
            self.oacc_kernelsImplicit[i] = list(set(self.oacc_kernelsImplicit[i]))
            # FIXME COMPRESSION
            # for fCall in self.active_calls_decl:
            #     if kernelDeclsBody[i].find(fCall[0])!=-1:
            #         funcCompArgList=[]
            #         m=re.search(fCall[0]+'\((.*?)\)',kernelDeclsBody[i],re.S)
            #         argList = m.group(1).split(',')
            #         for compVarObj in self.oacc_kernelsComp[i]:
            #             #print compVar 
            #             #print fCall[0]
            #             for arg in argList:
            #                 #print arg.strip()
            #                 if compVarObj.varName == arg.strip():
            #                     funcCompArgList.append([argList.index(arg),compVarObj.varName])
            #             #print funcCompArgList  
#           #          kernelDecl=kernelDecl.replace(m.group(0),'__accelerator_'+fCall[0]+'('+','.join(argList)+')')
            #         self.recursive_compVar_tracer(fCall[0],funcCompArgList)
            # print self.func_comp_vars


    def util_get_var_type(self, kernelId, vname):
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        if vname in scopeVarsNames:
            return scopeVarsTypes[scopeVarsNames.index(vname)]
        else:
            print_error('variable type not found', ['variable name: '+vname])

    def find_kernel_undeclaredVars_and_args(self, kernelBody, kernelId):
        # here we look for variable 
        # and return their declarations, if they are not already declared
        # here, conservatively, we define all variables as the function argument
        if USEPYCPARSER:
            root=self.pycparser_getAstTree(kernelBody)
        else:
            #srcML
            #root=srcml_code2xml(kernelBody)
            # preprocess replaces in the real name of variables, if there is a define directive in the kernels regions
            root=srcml_code2xml(self.preprocess_by_gnu_cpp(kernelBody))
            if DEBUGSRCMLC: print 'Error 1862! Unimplemented AST generator!'
        # first find all the function calls IDs
        allFc=[]
        if USEPYCPARSER:
            for fcc in root.findall(".//FuncCall/ID"):
                #allFc.append(str(fcc.get('uid')).strip().replace(',','')) #FIXME
                allFc.append(str(fcc.get('uid')).strip()) 
            allFc=list(set(allFc))
        else:
            #srcML
            allFc=list(srcml_get_fcn_calls(root))
            #srcml_fcn_details(allFc)
            if DEBUGSRCMLC: print 'Error 1874! Unimplemented AST generator!'
            #exit(-1)
        if VERBOSE==1 and len(allFc)>0:
            print 'kernels region > Function calls: '+','.join(allFc)
        # second, find all the ID tags
        allIds=[]
        if USEPYCPARSER:
            allIds=root.findall(".//ID")
        else:
            #srcML
            if DEBUGCPARSER>0:
                print 'kernel XML > '+tostring(root)
            #print self.oacc_extra_symbols
            allIds=srcml_get_all_ids(root)+self.oacc_extra_symbols[kernelId]
        if DEBUGCPARSER==1 and len(allIds)>0:
            #print 'identifiers found in the kernels region > : '+', '.join(allIds)
            if DEBUGSRCMLC: print 'Error 1891! Unimplemented AST generator!'
            #exit(-1)
        vars=[]
        for var in allIds:
            #print var
            if USEPYCPARSER:
                vnm=str(var.get('uid'))
            else:
                vnm=var
            func=True
            try :
                allFc.index(vnm.strip())
            except :
                func=False
            if not func:
                vars.append(vnm.strip())
            else:
                self.active_calls.append(vnm.strip())

        # here we have vars and allFc
        vars=list(set(vars))
        if VERBOSE==1 and len(vars)>0:
            print 'kernels region > Variables: '+', '.join(vars)
        # third, removed defined variables
        try:
            vars.remove(self.prefix_kernel_uid_x)
            vars.remove(self.prefix_kernel_uid_y)
            vars.remove(self.prefix_kernel_uid_z)
        except:
            notThreeDim=True
        if USEPYCPARSER:
            declVarList=root.findall(".//Decl")
        else:
            declVarList=srcml_get_declared_vars(root)
            if DEBUGCPARSER>0:
                print 'declared vars are: > '+','.join(declVarList)
            if DEBUGSRCMLC: print 'Error 1929! Unimplemented AST parser!'
            #exit(-1)
        for var in declVarList:
            try :
                if USEPYCPARSER:
                    vnm=str(var.get('uid'))
                else:
                    vnm=var
                # exclude declared vars
                if DEBUGVAR:
                    print 'variable is defined: '+vnm.strip()
                vars.remove(vnm.strip())
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
        if DEBUGPRIVRED:
            self.debug_dump_privredInfo('private',privInfo)
            self.debug_dump_privredInfo('reduction',reduInfo)
        # five, listing all smc variables to this kernel
        smcInfo=self.oacc_smc_getVarNames(kernelId)
        if DEBUGSMC:
            self.debug_dump_smcInfo(smcInfo)
        # six, find the function arguments and implicit copies
        scopeVarsNames=self.oacc_kernelsVarNams[kernelId]
        scopeVarsTypes=self.oacc_kernelsVarTyps[kernelId]
        if DEBUGVAR:
            for i in range(0,len(scopeVarsNames)):
                print 'traced var: '+scopeVarsNames[i]+' of '+scopeVarsTypes[i]
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
                # we handle iterators separately 
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
            if len(self.oacc_kernelsManualPtrs) and self.oacc_kernelsManualPtrs[kernelId]!='':
                for mv in self.oacc_kernelsManualPtrs[kernelId].split(','):
                    if mv.strip()==vars[i].strip():
                        manualvar=True
                        break
            # 4- private/reduction variables (exclude from functionArgs for now)
            priv=False # if true, exclude the variable from functionArgs
            redu=False # if true, include a pointer to this variable
            for [priredV, priredI, priredO, corr, typ, depth] in self.unique_priv_list(privInfo+reduInfo):
                if priredV.strip()==vars[i].strip():
                    if priredO=='U':
                        priv=True
                    else:
                        redu=True
                    if DEBUGPRIVRED:
                        print 'varname="'+priredV.strip()+'" is     equal to "'+vars[i].strip()+'"'
                elif DEBUGPRIVRED:
                    print 'varname="'+priredV.strip()+'" is not equal to "'+vars[i].strip()+'"'
            if WARNING and priv and redu:
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
                try:
                    if self.target_platform=='ISPC' and (vars[i]=='__ispc_thread_idx' or vars[i]=='__ispc_n_threads'):
                        # variables to run over ISPC tasks
                        thisVarType='unsigned int'
                    else:
                        idx=scopeVarsNames.index(vars[i])
                        thisVarType=scopeVarsTypes[idx]
                    if thisVarType.count('*')!=0:
                        # 7- is pointer
                        pointr=True
                    scalar_copy=(thisVarType.count('*')==0) and manualvar and (not self.container_class_supported(thisVarType))
                    is_container = self.container_class_supported(thisVarType)
                    if is_container:
                        arg_type=self.container_class_pseudo(thisVarType)
                    else:
                        arg_type=thisVarType
                    arg_type+='* ' if (redu or scalar_copy) else ' '
                    arg_name=vars[i]
                    arg_name+=('__ipmacc_scalar' if scalar_copy and (not (redu and manualvar)) else '')
                    arg_name+=('__ipmacc_deviceptr' if autovar else '')
                    arg_name+=('__ipmacc_reductionarray_internal' if redu else '')
                    arg_name+=('__ipmacc_container' if is_container else '')
                    arg_name =('__ipmacc_opt_readonlycache'+arg_name if pointr else arg_name)
                    function_args.append(arg_type+arg_name)
                    #function_args.append(thisVarType+('* ' if redu else ' '))
                    #function_args.append(thisVarType+('* ' if (redu or not pointr)else ' ')+(vars[i]+('__ipmacc_scalar' if ((not pointr) and (not redu)) else '')))
                except:
                    if self.target_platform=='ISPC' and (vars[i]=='programCount' or vars[i]=='taskIndex0'):
                        # skip these two variable, these are defined in the export/task body by ISPC compiler.
                        undef=True
                    elif WARNING and not self.iskeyword_or_predeftyp(vars[i]):
                        print 'warning: Could not determine the type of identifier used in the kernel: '+vars[i]
                        print '\tignoring undefined variable, maybe it\'s a macro or a field in struct.'
                        print '\tavailables are: '+','.join(scopeVarsNames)
                    undef=True
                    #exit (-1)
            # 8- track implicit copies
            if WARNING and manualvar and autovar:
                print 'warning: Confusion on declaration of variable `'+vars[i]+'`'
            elif not(undef or manualvar or autovar or (not pointr)):
                # the variable is implicitly defined on device
                # handle the copy-in/copyout
                implicitCopies.append(vars[i].strip())
        # seven, perform implicit copies
        self.perform_implicit_copy(kernelId,scopeVarsNames,scopeVarsTypes,implicitCopies)
        # eight, construct declaration of loop iterators (both parallel and sequential)
        code=''
#        for i in kernelLoopIteratorsPar:
#            code+='int '+i+';\n'
        if DEBUGITER:
            print 'iterators> '+', '.join(kernelLoopIteratorsPar+kernelLoopIteratorsSeq)
        iteratorsList=list(set(kernelLoopIteratorsPar+kernelLoopIteratorsSeq))
        for i in iteratorsList:
            defOutKernel=True
            try :
                idx=scopeVarsNames.index(i)
                code+=scopeVarsTypes[idx]+' '+i+';\n'
            except:
                defOutKernel=False
                if WARNING: print 'warning: Could not determine the type of loop iterator used in the kernel: '+i
            if not defOutKernel:
                # TODO: avoid warning
                # check inside the kernel for the definition 
                # if not exist report error
                if WARNING: print('\tunimplemented fallback')
                #exit(-1)

        # manage atomic operations and necessary arguments
        atomicBlocks=[]
        for [atomicKId, atomicId, atomicBody, atomicClause] in self.oacc_atomicReg:
            if atomicKId == kernelId:
                atomicBlocks.append([atomicId, atomicBody, atomicClause])
        if len(atomicBlocks)>0:
            function_args.append(self.atomicRegion_locktype+' * '+self.prefix_kernel_atomicLocks)
        
        # perforation expansion rate passed as argument
        for idx, [prfr_kernelId, prfr_Expansion] in enumerate(self.perforationrates):
            if str(prfr_kernelId).strip()==str(kernelId):
                function_args.append('float __ipmacc_prfr_'+str(idx))#+' = '+prfr_Expansion)

        # report stats
        if VERBOSE==1:
            if len(function_args)>0: print 'kernels region > kernel arguments: '+', '.join(function_args)
            if len(self.oacc_kernelsAutomaPtrs)>0: print 'kernels region > automatic vars (deviceptr)                 > '+self.oacc_kernelsAutomaPtrs[kernelId]
            if len(self.oacc_kernelsManualPtrs)>0: print 'kernels region > manual    vars (copy in, copy out, create) > '+self.oacc_kernelsManualPtrs[kernelId]
            print 'kernels region > implicit copy peformed for                 > '+','.join(implicitCopies)
        # return function args and early declaration part
        return [function_args, code, implicitCopies, privInfo, reduInfo, smcInfo]

    def kernel_forSize_CReadable(self, l):
        if len(l)==1 and not (type(l[0]) is str):
            return self.kernel_forSize_CReadable(l[0])
        mmax=[]
        prod=[]
        for ch in l:
            if type(ch) is str:
                prod.append(ch)
            else:
                j=self.kernel_forSize_CReadable(ch)
                if j!='':
                    mmax.append(j)
        if len(prod)>0 and len(mmax)>0:
            return '*'.join(prod)+'*'+'IPMACC_MAX'+str(len(mmax))+'('+','.join(mmax)+')'
        elif len(prod)>0:
            return '('+'*'.join(prod)+')'
        elif len(mmax)>0:
            return 'IPMACC_MAX'+str(len(mmax))+'('+','.join(mmax)+')'
        else:
            return ''

    def kernel_forSize_list_matrix(self, root, currentdepth, kernel_id, output):
        # currentdepth should start from 1
        # determining the total reguired threads for parallelism of every loop
        # and marking the lastlevel loop (leaves)
        # dedicated to nested loops mapped to multi-dimensional thread-blocks
        offset=0
        if root.tag=='pragma' and root.attrib['directive']=='algorithm':
            itercount=self.algo_get_preferred_width(kernel_id) #self.algorithm_execution_width
            if currentdepth>len(output):
                # append new dimension
                output.append([])
            output[currentdepth-1].append(['a',itercount])
        elif root.tag=='for' and root.attrib['independent']=='true':
            if root.attrib['gang']!='' and root.attrib['vector']!='':
                itercount='('+root.attrib['gang']+'*'+root.attrib['vector']+')'
            else:
                itercount=self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'),root.attrib.get('boundary'))
            [prfr_ty, prfr_prm, prfr_en, prfr_fix] = self.perforation_read_clause(root.attrib['perforation'])
            if prfr_en:
                if self.perforationshrink:
                    if prfr_ty=='stride':
                        itercount = '(('+itercount+')/((float)'+prfr_prm[0]+'))'
                    elif prfr_ty=='rate':
                        itercount = '(('+itercount+')*(1.0-('+prfr_prm[0]+')))'
                    else:
                        print 'unknown perforation type.'
                        print 'aborting()'
                        exit(-1)
            if currentdepth>len(output):
                # append new dimension
                output.append([])
            output[currentdepth-1].append(['f',itercount])
            offset+=1
        for ch in root:
            self.kernel_forSize_list_matrix(ch, currentdepth+offset, kernel_id, output)

    # def kernel_forSize_list(self, root, lookingdepth, currentdepth, kernel_id):
    #     # determining the total reguired threads for parallelism of every loop
    #     # and marking the lastlevel loop (leaves)
    #     # dedicated to nested loops mapped to multi-dimensional thread-blocks
    #     itercount=''
    #     if root.tag=='pragma' and root.attrib['directive']=='algorithm':
    #         itercount=self.algo_get_preferred_width(kernel_id) #self.algorithm_execution_width
    #     elif root.tag=='for' and root.attrib['independent']=='true' and lookingdepth==currentdepth:
    #         if root.attrib['gang']!='' and root.attrib['vector']!='':
    #             itercount='('+root.attrib['gang']+'*'+root.attrib['vector']+')'
    #         else:
    #             itercount=self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'),root.attrib.get('boundary'))
    #     else:
    #         if root.tag=='for' and root.attrib['independent']=='true':
    #             offset=1
    #         else:
    #             offset=0
    #         for ch in root:
    #             itercount+=self.kernel_forSize_list(ch, lookingdepth, currentdepth+offset, kernel_id)
    #     return itercount

    def label_for_depth(self, root, algorithm_ranks):
        l=0
        for ch in root:
            l=max(l,self.label_for_depth(ch,algorithm_ranks))
        if root.tag=='pragma' and root.attrib['directive']=='algorithm':
            #print 'CLEAR ME WHEN IT IS STABLE'
            root.attrib['reversedepth'] = str(l)
            algorithm_ranks.append(str(l))
            return l+1
        elif root.tag=='for' and root.attrib['independent']=='true':
            root.attrib['reversedepth'] = str(l)
            #print 'setting a label> '+str(l)
            return l+1
        else:
            return l
    def find_kernel_forSize_Recursive(self, root, algorithm_ranks):
        # determining the total reguired threads for parallelism of every loop
        # and marking the lastlevel loop (leaves)
        accumulation=[]
        horizon=[]
        for ch in root:
            t=self.find_kernel_forSize_Recursive(ch, algorithm_ranks)
            if len(t)>0:
                horizon.append(t)
        if len(horizon)>0:
            accumulation.append(horizon)
        if root.tag=='pragma' and root.attrib['directive']=='algorithm':
            itercount='1' # single thread-block for algorithm
            accumulation.append(itercount) #FIXME
            return accumulation
        elif root.tag=='for' and root.attrib['independent']=='true':
            # count iterations 
            if root.attrib['gang']!='' and root.attrib['vector']!='':
                itercount='('+root.attrib['gang']+'*'+root.attrib['vector']+')'
            else:
                itercount=self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'),root.attrib.get('boundary'))
            # consider perforation
            [prfr_ty, prfr_prm, prfr_en, prfr_fix] = self.perforation_read_clause(root.attrib['perforation'])
            if prfr_en:
                if self.perforationshrink:
                    if prfr_ty=='stride':
                        itercount = '(('+itercount+')/((float)'+prfr_prm[0]+'))'
                    elif prfr_ty=='rate':
                        itercount = '(('+itercount+')*(1.0-('+prfr_prm[0]+')))'
                    else:
                        print 'unknown perforation type.'
                        print 'aborting()'
                        exit(-1)

            # mark if this loop is on the same rank as an algorithm 
            try:
                algorithm_ranks.index(root.attrib['reversedepth'])
                root.attrib['algoonrank'] = 'true'
            except:
                root.attrib['algoonrank'] = 'false'
            # keep track of the level/dimension
            if len(accumulation)==0:
                root.attrib['lastlevel']='true'
                accumulation.append(itercount) #FIXME
                #accumulation.append(root.attrib.get('terminate')) 
                root.attrib['dimloops']=self.kernel_forSize_CReadable(accumulation)
            else:
                root.attrib['lastlevel']='false'
                root.attrib['dimloops']=self.kernel_forSize_CReadable(accumulation)
                accumulation.append(itercount) #FIXME
                #accumulation.append(root.attrib.get('terminate'))
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
            return [iterator_p, '@'+self.count_loopIter(root.attrib.get('init'),root.attrib.get('terminate'),root.attrib.get('incoperator'),root.attrib.get('incstep'),root.attrib.get('boundary'))+size, iterator_s]
        return [iterator_p, size, iterator_s]

    def carry_loopAttr2For(self, root, independent, private, reduction, gangs, vectors, smcs, perforation):
        # get kernels region and go through to carry loop clauses to the corresponding for
        # mark independent loops, private vars, reduction vars
        if DEBUGLD:
            print 'gang> '+gangs+' vector> '+vectors
        if root.tag=='pragma':
            if root.attrib.get('directive')=='kernels':
                for ch in root:
                    self.carry_loopAttr2For( ch, False, private, reduction, gangs, vectors, smcs, perforation)
            elif root.attrib.get('directive')=='loop':
                [indep, priv, reduc, gang, vector, smc, perfor]=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                for ch in root:
                    self.carry_loopAttr2For(ch, indep, private+priv, reduction+reduc, gangs+gang, vectors+vector, smcs+smc, perfor)
            elif root.attrib.get('directive')=='cache':
                for ch in root:
                    self.carry_loopAttr2For( ch, False, private, reduction, gangs, vectors, smcs, perforation)
            elif root.attrib.get('directive')=='atomic' or root.attrib.get('directive')=='algorithm':
                righton = True
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
            # cut gang
            root.attrib['gang']=gangs
            # cut vector
            root.attrib['vector']=vectors
            # cut smc
            root.attrib['smc']=','.join(smcs)
            # cut perforation 
            root.attrib['perforation']=perforation
            # go through the childs
            for ch in root:
                self.carry_loopAttr2For(ch, False, [], [], '', '', [], '')
            if DEBUGLD:
                # print loop attribute
                print self.print_loopAttr(root)
    def perforation_gen_expansion(self, kerId):
        decl = ''
        if len(self.perforationrates)>0:
            for prfr_idx, [prfr_kernelId, prfr_Expansion] in enumerate(self.perforationrates):
                if str(prfr_kernelId)==str(kerId):
                    decl += 'float __ipmacc_prfr_'+str(prfr_idx)+' = '+prfr_Expansion+';\n'
        return decl

    def perforation_gen_fix(self, pointername, index, vname, prfr_fix):
        code  = ''
        code += '{\n'
        code += '// fix '+pointername+index+'\n'
        if   prfr_fix=='fixcpy':
            code += pointername+index+'='+vname+';\n'
        elif prfr_fix=='fixavg':
            code += pointername+index+'= (__shfl_down('+vname+',1)+__shfl_up('+vname+',1)+'+vname+')/3.0;\n'
        elif prfr_fix=='fixmin':
            code += pointername+index+'= min(min(__shfl_down('+vname+',1),__shfl_up('+vname+',1)),'+vname+');\n'
        elif prfr_fix=='fixmax':
            code += pointername+index+'= max(max(__shfl_down('+vname+',1),__shfl_up('+vname+',1)),'+vname+');\n'
        elif prfr_fix=='fixwav':
            code += pointername+index+'= (__shfl_down('+vname+',1)+__shfl_up('+vname+',1)+2*'+vname+')/4.0;\n'
        else:
            print_error('unimplemented perforation fix method', ['perforation method: '+prfr_fix])
        code += '}\n'
        return code
    def perforation_read_clause(self, clause):
        prfr_en = False
        prfr_ty = ''
        prfr_prm = []
        if clause!='':
            prfr_ty = clause.split(',')[0]
            prfr_prm= clause.split(',')[1:]
            prfr_en = prfr_ty!=''
        return [prfr_ty, prfr_prm, prfr_en, self.perforationfixtyp]

    def get_dim_iterator(self, depth):
        if   depth=='0':
            return self.prefix_kernel_uid_x
        elif depth=='1':
            return self.prefix_kernel_uid_y
        elif depth=='2':
            return self.prefix_kernel_uid_z
        else:
            print 'Fatal Error! More than 3 nested loops are not supported for multi-dimensional thread-blocks. Set GENMULTIDIMTB to False inn codegen.py [depth is '+str(depth)+']'
            exit(-1)

    def var_kernel_genPlainCode(self, id, root, nesting):
        code=''
        try:
            if root.tag=='pragma':
                if root.attrib.get('directive')=='kernels':
                    compVarList=[]
                    for [i0, i3] in clauseDecomposer_break(root.attrib.get('clause')):
                        if str(i0).strip()=='compression':
                            for j in str(i3).replace(' ','').strip().split(','):
                                var=str(j).split('[')[0]
                                compVarList.append(compVar(var))
                    self.oacc_kernelsComp.append(compVarList)
                    #retrieve compression clause and `define a(index) decompress() 
                    code=code+'{\n'
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting)
                    code=code+'}\n'
                elif root.attrib.get('directive')=='loop':
                    [indep, priv, reduc, gang, vector, smc, perforation]=self.oacc_clauseparser_loop_isindependent(root.attrib.get('clause'))
                    self.oacc_kernelsConfig_update(id, vector if vector!='' else 'PREDEF', nesting)
                    for ch in root:
                        #print str(indep)
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting)
                elif root.attrib.get('directive')=='cache':
                    # backtrack
                    codeinside = ''
                    for ch in root:
                        codeinside+=self.var_kernel_genPlainCode(id, ch, nesting)
                    #print codeinside
                    code+='//go on with the clause '+root.attrib.get('clause')+'\n'
                    # cache region open
                    smcId=len(self.oacc_loopSMC)
                    variables=root.attrib.get('clause').strip()[1:-1]
                    code+=self.prefix_kernel_smc_fetch+str(smcId)+'();\n'
                    self.oacc_loopSMC.append([id,variables,codeinside])
                    code+=codeinside
                    # cache region close
                    code+=self.prefix_kernel_smc_fetchend+str(smcId)+'();\n'
                    code+='//end up with the clause '+root.attrib.get('clause')+'\n'
                elif root.attrib.get('directive')=='atomic':
                    if DEBUGATOMIC: print 'atomic directive found!'
                    # atomic region
                    atomicId=len(self.oacc_atomicReg)
                    atomicBody=''
                    for ch in root:
                        atomicBody+=self.var_kernel_genPlainCode(id, ch, nesting)
                    self.oacc_atomicReg.append([id, atomicId, atomicBody, root.attrib.get('clause')])
                    code+='//atomic region \n'+self.prefix_kernel_atomicRegion+str(atomicId)+'();\n'+atomicBody
                elif root.attrib.get('directive')=='algorithm':
                    # algorithm region
                    algoId=len(self.oacc_algoReg)
                    algoBody=''
                    self.algo_update_preferred_width(id, root.attrib.get('clause'))
                    self.oacc_kernelsConfig_update(id, self.algo_get_preferred_width(id), nesting) #self.algorithm_execution_width)
                    for ch in root:
                        algoBody+=self.var_kernel_genPlainCode(id, ch, nesting)
                    if algoBody.strip()!='':
                        print 'algorithm directive is single line, does not apply to a region!\n'
                        exit(-1)
                    self.oacc_algoReg.append([id, algoId, algoBody, root.attrib.get('clause'), root.attrib.get('reversedepth')])
                    code+='//algorithm region \n'+self.prefix_kernel_algoRegion+str(algoId)+'();\n'+algoBody
                else:
                    print('Invalid: '+root.attrib.get('directive')+' directive in region!')
                    exit(-1)
            elif root.tag=='for':
                if (self.target_platform=='CUDA' or self.target_platform=='OPENCL') and root.attrib['independent']=='true': #independent:
                    [prfr_ty, prfr_prm, prfr_en, prfr_fix] = self.perforation_read_clause(root.attrib['perforation'])
                    if prfr_en:
                        print '  warning: loop undergoes perforation:', root.attrib['perforation']
                        if root.attrib.get('incoperator')!='-' and root.attrib.get('incoperator')!='+':
                            print_error('unimplemented increment operator under perforation', ['inc operator: '+root.attrib.get('incoperator')])
                    if DEBUGLD:
                        print 'for loop of -> '+root.attrib['iterator']+' -> '+root.attrib['dimloops']
                    # generate indexing
                    dimension_iterator=self.get_dim_iterator(root.attrib.get('reversedepth'))
                    # iterating value 
                    if root.attrib.get('incoperator')=='+' or root.attrib.get('incoperator')=='-':
                        ex_incstep_nscald = root.attrib.get('incstep')
                        ex_incstep_scaled = '(__ipmacc_prfr_'+str(len(self.perforationrates))+'*'+root.attrib.get('incstep')+')'
                        iteratorVal_scaled_prev=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_scaled+'*('+dimension_iterator+'-1)'
                        iteratorVal_scaled_next=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_scaled+'*('+dimension_iterator+'+1)'
                        iteratorVal_scaled_iter=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_scaled+'*('+dimension_iterator+')'
                        iteratorVal_nscald_prev=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_nscald+'*('+dimension_iterator+'-1)'
                        iteratorVal_nscald_next=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_nscald+'*('+dimension_iterator+'+1)'
                        iteratorVal_nscald_iter=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+ex_incstep_nscald+'*('+dimension_iterator+')'
                        if (not prfr_en) or (not self.perforationshrink):
                            iteratorVal = iteratorVal_nscald_iter
                        else:
                            iteratorVal = iteratorVal_scaled_iter
                        if prfr_en:
                            if prfr_ty=='stride':
                                expansion_rate = prfr_prm[0]
                                self.perforationrates.append([id, expansion_rate])
                            elif prfr_ty=='rate':
                                expansion_rate = '(1/(1-'+prfr_prm[0]+'))'
                                self.perforationrates.append([id, expansion_rate])
                            else:
                                print 'unknown perforation type.'
                                print 'aborting()'
                                exit(-1)
                    elif root.attrib.get('incoperator')=='/' or root.attrib.get('incoperator')=='*':
                        powerfunction = 'pown((float)'+root.attrib.get('incstep')+',(int)'+dimension_iterator+')' if self.target_platform=='OPENCL' else 'powf((float)'+root.attrib.get('incstep')+',(float)'+dimension_iterator+')'
                        iteratorVal=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+powerfunction+''
                        if prfr_en and prfr_fix!='non':
                            powerfunction = 'pown((float)'+root.attrib.get('incstep')+',((int)'+dimension_iterator+'+1))' if self.target_platform=='OPENCL' else 'powf((float)'+root.attrib.get('incstep')+',(float)('+dimension_iterator+'+1))'
                            iteratorVal_scaled_next=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+powerfunction+';'
                    else:
                        print 'unsupported loop increment operator> '+root.attrib.get('incoperator')
                        exit(-1)
                    if prfr_en:
                        code+='int __ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_prev ='+iteratorVal_scaled_prev+';\n'
                        code+='int __ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_next ='+iteratorVal_scaled_next+';\n'
                        code+='int __ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_iter ='+iteratorVal_scaled_iter+';\n'
                        code+='int __ipmacc_internal_it_nscald_'+root.attrib.get('iterator')+'_next ='+iteratorVal_nscald_next+';\n'
                        code+='int __ipmacc_internal_it_nscald_'+root.attrib.get('iterator')+'_prev ='+iteratorVal_nscald_prev+';\n'
                        code+='int __ipmacc_internal_it_nscald_'+root.attrib.get('iterator')+'_iter ='+iteratorVal_nscald_iter+';\n'
                        code+='int __ipmacc_internal_it_'+root.attrib.get('iterator')+'_missing_fw = '+iteratorVal+root.attrib.get('incoperator')+'1;\n' # iterator that is dropped
                        code+='int __ipmacc_internal_it_'+root.attrib.get('iterator')+'_missing_bw = '+iteratorVal+root.attrib.get('incoperator')+'1*(-1);\n' # iterator that is dropped
                        code+='bool __ipmacc_internal_next_is_dropped = '+'__ipmacc_internal_it_'+root.attrib.get('iterator')+'_missing_fw!=__ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_next'+';\n'
                        code+='bool __ipmacc_internal_this_is_dropped = '+'__ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_prev!=('+'__ipmacc_internal_it_scaled_'+root.attrib.get('iterator')+'_iter'+');\n'
                        if prfr_fix!='non':
                            code+='__ipmacc_internal_n_output_to_cache\n'
                    code+=root.attrib.get('declared')+' ' #append iterator type if it is carried
                    code+=root.attrib.get('iterator')+'='+iteratorVal+';\n'
                    # generate work-sharing control statement
                    if root.attrib.get('gang')!='' and root.attrib.get('vector')!='':
                        # FIXME
                        print 'unimplemented configuration:'
                        print 'gang and vector are enabled together.'
                        print 'aborting()'
                        exit(-1)
                        code+='if('+self.prefix_kernel_uid_x+'<('+root.attrib.get('gang')+'*'+root.attrib.get('vector')+'*'+root.attrib.get('dimloops')+'))'
                        code+='for('+root.attrib.get('iterator')+'='+iteratorVal+'; '+root.attrib.get('boundary')+'; '+root.attrib.get('iterator')+'+='+root.attrib.get('gang')+'*'+root.attrib.get('vector')+')\n'
                    elif root.attrib['algoonrank']=='true':
                        code+='for('+root.attrib.get('iterator')+'='+iteratorVal+'; '+root.attrib.get('boundary')+'; '+root.attrib.get('iterator')+'+=blockDim.x /*assumed algorithm is always in the inner loop*/)\n'
                    else:
                        code+='if('+root.attrib.get('boundary')+')\n'
                    # private/reduction
                    if root.attrib.get('private')!='' or root.attrib.get('reduction')!='':
                        # generate private/reduction declaration
                        separator=(',' if (root.attrib.get('private')!='' and root.attrib.get('reduction')!='') else '')
                        variables=root.attrib.get('private')+separator+root.attrib.get('reduction')
                        code+='{ //opened for private and reduction\n'
                        code=code+'/*private:'+variables+'*/\n'
                        code=code+self.prefix_kernel_privred_region+str(len(self.oacc_loopPrivatizin))+'();'+'\n'
                        self.oacc_loopPrivatizin.append([id,variables])
                    # go through children
                    codeinside = ''
                    for ch in root:
                        codeinside+= self.var_kernel_genPlainCode(id, ch, nesting+1)
                    if prfr_en:
                        if DEBUGPRFR: print codeinside
                        [prfr_kernel_writes, prfr_kernel_reads] = self.find_kernel_writes(codeinside, id)
                        if DEBUGPRFR:
                            for [arraccs, indecis, dependt, arraccs_loc, assignmentIdx, assignmentOpr, writeIdx_str, writeIdx_end, writeIdx_loc] in prfr_kernel_writes:
                                print '========='
                                print 'ARRAY NAME:', arraccs
                                print 'INDEX EXPR:', indecis
                                print 'DEPND. VAR:', dependt
                                print 'ACCESS COD:', codeinside[arraccs_loc:arraccs_loc+10], '...'
                                print 'ASSIGNMTOP:', assignmentOpr
                                print 'WRITE EXPR:', codeinside[writeIdx_str:writeIdx_end], '...'
                                print 'WRITE  IDX:', writeIdx_loc
                                print '========='
                            for [arraccs, indecis, dependt, arraccs_loc] in prfr_kernel_reads:
                                print '========='
                                print 'ARRAY NAME:', arraccs
                                print 'INDEX EXPR:', indecis
                                print 'DEPND. VAR:', dependt
                                print 'ACCESS COD:', codeinside[arraccs_loc:arraccs_loc+10], '...'
                                print '========='
                        if prfr_fix!='non':
                            codeinside+='// perforation fixup\n'
                            codeinside+='if(__ipmacc_internal_next_is_dropped)\n{\n'
                            codeinside+='int '+root.attrib.get('iterator')+'='+'__ipmacc_internal_it_'+root.attrib.get('iterator')+'_missing_fw;\n'
                            codeinside+='if('+root.attrib.get('boundary')+')\n{\n'
                            code_cacheoutput = ''
                            for tmp_idx in range(len(prfr_kernel_writes)-1,-1,-1):
                                [arraccs, indecis, dependt, arraccs_loc, assignmentIdx, assignmentOpr, writeIdx_str, writeIdx_end, writeIdx_loc] = prfr_kernel_writes[tmp_idx]
                                variabletype = self.util_get_var_type(id, arraccs).replace('*','').strip()
                                code_cacheoutput += variabletype+' __ipmacc_internal_output_'+str(tmp_idx)+';\n'
                                codeinside = codeinside[0:writeIdx_str] + '__ipmacc_internal_output_' + str(tmp_idx) + ' = ' + codeinside[writeIdx_str:]
                                codeinside += self.perforation_gen_fix(arraccs, indecis, '__ipmacc_internal_output_' + str(tmp_idx), prfr_fix)
                            codeinside+='}\n'
                            codeinside+='}\n'
                            code = code.replace('__ipmacc_internal_n_output_to_cache', code_cacheoutput)
                    # smc
                    smcId=len(self.oacc_loopSMC)
                    if root.attrib.get('smc')!='' and root.attrib['independent']=='true':
                        code+='{ // opened for smc fetch\n'
                        variables=root.attrib.get('smc')
                        code+=self.prefix_kernel_smc_fetch+str(smcId)+'();\n'
                        self.oacc_loopSMC.append([id,variables,codeinside])
                        code+=codeinside
                        code+=self.prefix_kernel_smc_fetchend+str(smcId)+'();\n'
                        code+='} // closed for smc fetch end\n'
                    else:
                        code+=codeinside
                    if root.attrib.get('reduction')!='':
                        # generate reduction operations
                        variables=root.attrib.get('reduction')+':'+str(nesting)
                        code=code+'/*reduction:'+variables+'*/\n'
                        code=code+self.prefix_kernel_reduction_region+str(len(self.oacc_loopReductions))+'();\n'
                        self.oacc_loopReductions.append([id,variables])
                    if root.attrib.get('private')!='' or root.attrib.get('reduction')!='':
                        code+='} // closed for reduction-end\n'
                    # terminate if statement
                    code=code+'\n'
                elif self.target_platform=='ISPC':
                    # private/reduction
                    if root.attrib.get('private')!='' or root.attrib.get('reduction')!='':
                        # generate private/reduction declaration
                        separator=(',' if (root.attrib.get('private')!='' and root.attrib.get('reduction')!='') else '')
                        variables=root.attrib.get('private')+separator+root.attrib.get('reduction')
                        code+='{ //opened for private and reduction\n'
                        code=code+'/*private:'+variables+'*/\n'
                        code=code+self.prefix_kernel_privred_region+str(len(self.oacc_loopPrivatizin))+'();'+'\n'
                        self.oacc_loopPrivatizin.append([id,variables])
                    #if root.attrib['independent']=='true' and root.attrib['lastlevel']=='true':
                    if root.attrib['independent']=='true' and root.attrib['lastlevel']=='true':
                        # parallelize this loop over the SIMD 
                        #print root.attrib
                        if root.attrib.get('incoperator')=='+' and root.attrib.get('incstep')=='1':
                            # special case, use foreach
                            #print root.attrib
                            code+='uniform int __ispc_loop_initial = '+root.attrib.get('init')+';\n'
                            code+='foreach( '+root.attrib.get('iterator')+'= __ispc_loop_initial ... '+root.attrib.get('terminate')+')\n'
                            extra_symbols = self.oacc_extra_symbols[id]
                            extra_symbols = extra_symbols +  srcml_get_all_ids(srcml_code2xml('for('+root.attrib.get('initial')+'; '+root.attrib.get('boundary')+'; '+root.attrib.get('increment')+'){}'))
                            self.oacc_extra_symbols[id] = extra_symbols
                        else:    
                            dimension_iterator=self.get_dim_iterator(root.attrib.get('reversedepth'))
                            if root.attrib.get('incoperator')=='+' or root.attrib.get('incoperator')=='-':
                                iteratorVal=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+root.attrib.get('incstep')+'*('+dimension_iterator+')'
                            elif root.attrib.get('incoperator')=='/' or root.attrib.get('incoperator')=='*':
                                powerfunction = 'pown((float)'+root.attrib.get('incstep')+',(int)'+dimension_iterator+')' if self.target_platform=='OPENCL' else 'powf((float)'+root.attrib.get('incstep')+',(float)'+dimension_iterator+')'
                                powerfunction = 'pow((float)'+root.attrib.get('incstep')+', programIndex)'
                                iteratorVal=('('+root.attrib.get('init')+')'+root.attrib.get('incoperator'))+powerfunction+''
                            else:
                                print 'unsupported loop increment operator> '+root.attrib.get('incoperator')
                                exit(-1)
                            code+='\nint __ispc_loop_initial = '+iteratorVal+';\n'
                            code+='int __ispc_chunk_id=0;\n '
                            code+='for( '
                            code+=root.attrib.get('declared')+' ' #append iterator type if it is carried
                            code+=root.attrib.get('iterator')+'= __ispc_loop_initial;\n'
                            code+=root.attrib.get('boundary')+';\n'
                            if root.attrib.get('incoperator')=='+' or root.attrib.get('incoperator')=='-':
                                code+='__ispc_chunk_id+=1, '+root.attrib.get('iterator')+'= __ispc_loop_initial'+root.attrib.get('incoperator')+'(__ispc_chunk_id*programCount*'+root.attrib.get('incstep')+'))\n'
                            elif root.attrib.get('incoperator')=='*' or root.attrib.get('incoperator')=='/':
                                powerfunction = 'pow((float)'+root.attrib.get('incstep')+',(int)(__ispc_chunk_id*programCount))'
                                code+='__ispc_chunk_id+=1, '+root.attrib.get('iterator')+'= __ispc_loop_initial'+root.attrib.get('incoperator')+powerfunction+')\n'
                            else:
                                print 'unsupported loop increment operator> '+root.attrib.get('incoperator')
                                exit(-1)
                    elif root.attrib['independent']=='true' and nesting==0: # root.attrib['reversedepth']=='1':
                        code=code+self.code_gen_reversiFor('int '+root.attrib.get('iterator')+'=('+root.attrib.get('initial').split('=')[1]+') '+root.attrib.get('incoperator')+'taskIndex0/*__ispc_thread_idx*/',
                            root.attrib.get('boundary'),
                            root.attrib.get('iterator')+'='+root.attrib.get('iterator')+root.attrib.get('incoperator')+'__ispc_n_threads\n')+'\n'
                    else:
                        #for atr in root.attrib:
                        #    print atr+' '+root.attrib[atr]+'\n'
                        #exit(-1)
                        code=code+self.code_gen_reversiFor(root.attrib.get('initial'),root.attrib.get('boundary'),root.attrib.get('increment'))+'\n'
                    # go through childs
                    for ch in root:
                        code=code+self.var_kernel_genPlainCode(id, ch, nesting+1)
                    code=code+'\n'
                    if root.attrib.get('reduction')!='':
                        # generate reduction operations
                        variables=root.attrib.get('reduction')+':'+str(nesting)
                        code=code+'/*reduction:'+variables+'*/\n'
                        code=code+self.prefix_kernel_reduction_region+str(len(self.oacc_loopReductions))+'();\n'
                        self.oacc_loopReductions.append([id,variables])
                    if root.attrib.get('private')!='' or root.attrib.get('reduction')!='':
                        code+='} // closed for reduction-end\n'
                else:
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
            print 'exception! dumping the code: #'+str(getframeinfo(currentframe()).lineno)+'\n'+self.code+code
            print e
            exit(-1)
        return code

    def debug_dump_privredInfo(self, type, privredList):
        for [v, i, o, a, t] in privredList:
            print type+'> variable: '+v+' initialized: '+i+' operator: '+o+' assignee: '+str(a)+' type: '+t

    # get a list of pack of smcInfos and prints struct elements
    # input: list smcList
    # output: void   
    def debug_dump_smcInfo(self, smcList):
        #for [variable, type, smctype, pivot, dwrange, uprange, diverge, kid, dimlo, dimhi] in smcList:
        for [variable, type, smctype, pivot, dwrange, uprange, diverge, corr, dimlow, dimhigh, w_dwrange, w_uprange, dim2low, dim2high, pivot2, dw2range, up2range, w_dw2range, w_up2range, vcode] in smcList:
            print 'SMC info:'
            print '\tvariable: '+variable
            print '\ttype: '+type
            print '\tsmctype: '+smctype
            print '\tpivot: '+pivot
            print '\tdwrange: '+dwrange
            print '\tuprange: '+uprange
            try:
                print '\tlength: ', int(dwrange)+int(uprange)+1
            except:
                print '\tlength: ', dwrange+uprange+str(1)
            print '\tdivergent: '+diverge
            print '\tdimlow: '+dimlow
            print '\tdimhigh: '+dimhigh
            print '\tdwwrange: '+w_dwrange
            print '\tupwrange: '+w_uprange
            if dw2range!='' and up2range!='':
                print '\tpivot2: '+pivot2
                print '\tdwrange2: '+dw2range
                print '\tuprange2: '+up2range
                try:
                    print '\tlength2: ', int(dw2range)+int(up2range)+1
                except:
                    print '\tlength2: ', dw2range+up2range+str(1)
                print '\tdim2low: '+dim2low
                print '\tdim2high: '+dim2high
                print '\tdw2wrange: '+w_dw2range
                print '\tup2wrange: '+w_up2range
            print '\tcoderegion: '+vcode

    # @ cache directive
    # process base index variable (called pivot here) and 
    # verify if it's in the normal form: R*T+O
    # where T is an induction variable and O and R are expressions not derived from
    # induction variables.
    # input:  string pivot (base index variable)
    # input:  list loop_induction_vars_list (list of induction variables in this kernel)
    # input:  string code (kernel code)
    # output: True if normal, False otherwise
    def smc_cache_base_is_normal(self, pivot, loop_induction_vars_list, code):
        return True   # FIXME
        # this requires sophisticated lex/yacc to detect the normal form
        # will do upon releasing the compiler.
        print 'verifying cache index normal form:'
        print '\tbase index:', pivot
        [srcmlO1, srcmlO2, srcmlO3, srcmlO4] = srcml_get_dependentVars(srcml_code2xml(code), [pivot])
        # print '\t', srcmlO1
        # print '\t', srcmlO2
        # print '\t', srcmlO3
        print '\tform to verify:', srcmlO4 
        print '\tinduction variables in the kernel:', ','.join(loop_induction_vars_list)
        print '\tkernel code:', code.replace('\n', '\n\t\t')
        return False
    
    # @ cache directive
    # process base index variable and return R and O if index is normal (R*T+O)
    # input:  string pivot (base index variable)
    # input:  list loop_induction_vars_list (list of induction variables in this kernel)
    # input:  string code (kernel code)
    # output: True if normal, False otherwise
    def smc_cache_base_normal_get_RO(self, pivot, loop_induction_vars_list, code):
        return ['1', '0'] # FIXME

    # @ cache directive
    # process the code and if `call' might be called from a divergent path
    # input: string call (name of the function that is called in the code)
    # input: string code (kernel code)
    # output: True if divergent, False otherwise
    def smc_cache_is_divergent(self, call, code):
        return False # FIXME

    # @ cache directive
    # generate declaration statements; including shared memory allocation and pointer declarations
    # input: int kernelId (ID of the current kernel)
    # input: string kernelB (kernel body)
    # input: string p (pivot index of 1st dim)
    # input: string v (cache subarray/variable name)
    # input: string up (#of elements before pivot that are cached on 1st dim)
    # input: string dw (#of elements after pivot that are cached on 1st dim)
    # input: string up2range (#of elements before pivot that are cached on 2nd dim)
    # input: string dw2range (#of elements after pivot that are cached on 2nd dim)
    # input: string ctadimx ((thread block size dim.x)
    # input: string ctadimy ((thread block size dim.y)
    # input: string t (v data type)
    # input: bool subarrayndim (number of dimensions in subarray)
    # output: True if p is static to induction variables, otherwise False
    # output: True if pivot2 is static to induction variables, otherwise False
    # output: length of 1st dimension of cache allocated in shared memory
    # output: length of 2nd dimension of cache allocated in shared memory
    # output: string of declaration statments
    def oacc_smc_codegen_declaration(self, kernelId, kernelB, p, pivot2, v, up, dw, up2range, dw2range, ctadimx, ctadimy, t, subarrayndim):
        if subarrayndim>2:
            print_error('cache directive: unsupported multidimentional subarray.', [])
        if CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_COMMUN:
            prefix  = '__shared__ '
        elif CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_PRIVATE:
            prefix  = '' 
        else:
            print_error('cache: unknown pointer calculation method!', [])
        f_is_stataic_p = ''
        f_is_stataic_p2 = ''
        length = ''
        length_2 = ''
        decl ='\n/* declare the shared memory of '+v+' */\n'

        # if subarrayndim>=1:
        #     f_is_stataic_p = not self.is_function_of_iterator_var(kernelId,kernelB,p)
        #     length   = self.oacc_smc_squeez_size(ctadimy, up, dw, f_is_stataic_p, p, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB)
        #     decl+=prefix+' int '+self.prefix_kernel_smc_startpointer+v+';\n'
        #     decl+=prefix+' int '+self.prefix_kernel_smc_endpointer+v+';\n'
        #     decl+=self.prefix_kernel_smc_endpointer+v+'=-1;\n'
        #     decl+=self.prefix_kernel_smc_startpointer+v+'=-1;\n'
        if subarrayndim==1:
            f_is_stataic_p = not self.is_function_of_iterator_var(kernelId,kernelB,p)
            length   = self.oacc_smc_squeez_size(ctadimx, up, dw, f_is_stataic_p, p, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB)
            decl+=prefix+' int '+self.prefix_kernel_smc_startpointer+v+';\n'
            decl+=prefix+' int '+self.prefix_kernel_smc_endpointer+v+';\n'
            decl+=self.prefix_kernel_smc_endpointer+v+'=-1;\n'
            decl+=self.prefix_kernel_smc_startpointer+v+'=-1;\n'
            decl+='__shared__ '+t.replace('*','')+' '+self.prefix_kernel_smc_varpref+v+'['+length+'];\n'
        elif subarrayndim==2:
            f_is_stataic_p = not self.is_function_of_iterator_var(kernelId,kernelB,p)
            length   = self.oacc_smc_squeez_size(ctadimy, up, dw, f_is_stataic_p, p, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB)
            decl+=prefix+' int '+self.prefix_kernel_smc_startpointer+v+';\n'
            decl+=prefix+' int '+self.prefix_kernel_smc_endpointer+v+';\n'
            decl+=self.prefix_kernel_smc_endpointer+v+'=-1;\n'
            decl+=self.prefix_kernel_smc_startpointer+v+'=-1;\n'
            f_is_stataic_p2= not self.is_function_of_iterator_var(kernelId,kernelB,pivot2)
            length_2 = self.oacc_smc_squeez_size(ctadimx, up2range, dw2range, f_is_stataic_p2, pivot2, self.oacc_kernelsLoopIteratorsPar[kernelId], kernelB)
            decl+=prefix+' int '+self.prefix_kernel_smc_startpointer+v+'_2d;\n'
            decl+=prefix+' int '+self.prefix_kernel_smc_endpointer+v+'_2d;\n'
            decl+=self.prefix_kernel_smc_endpointer+v+'_2d=-1;\n'
            decl+=self.prefix_kernel_smc_startpointer+v+'_2d=-1;\n'
            decl+='__shared__ '+t.replace('*','')+' '+self.prefix_kernel_smc_varpref+v+'['+length+']['+length_2+'];\n'
        return [f_is_stataic_p, f_is_stataic_p2, length, length_2, decl]

    # @ cache directive
    # set boundary pointers for RBC and RBI
    # input: int kernelId (ID of the current kernel)
    # input: string kernelB (kernel body)
    # input: string p (pivot index of 1st dim)
    # input: string v (cache subarray/variable name)
    # input: string up (#of elements before pivot that are cached on 1st dim)
    # input: string dw (#of elements after pivot that are cached on 1st dim)
    # input: string up2range (#of elements before pivot that are cached on 2nd dim)
    # input: string dw2range (#of elements after pivot that are cached on 2nd dim)
    # input: string ctadimx ((thread block size dim.x)
    # input: string ctadimy ((thread block size dim.y)
    # input: string t (v data type)
    # input: bool isfusion (True if this subarray fetch can be merged with a previously generated code)
    # input: int fusionIdx (if isfusion, the fusion ID is returned in fusionSMC) 
    # input: bool f_is_stataic_p (True if p is static to induction variables, otherwise False)
    # input: bool f_is_stataic_p2 (True if pivot2 is static to induction variables, otherwise False)
    # input: bool subarrayndim (number of dimensions in subarray)
    # output: string of statments setting the boundary pointers
    # output: string of new kernelB
    def oacc_smc_codegen_set_boundary_pointers(self, kernelId, kernelB, p, pivot2, v, up, dw,\
            up2range, dw2range, ctadimx, ctadimy, t,\
            isfusion, fusionIdx, fusionSMC,\
            f_is_stataic_p, f_is_stataic_p2, ndim):
        #   start address
        datafetch = ''
        if isfusion:
            [tmp1, tmp2, tmp3, tmp4, tmp5, tmp6, tmp7]=fusionSMC[fusionIdx]
            # merge this fetch with previous one 
            tmp1='__fusion_merge_boundary_'+str(fusionIdx)+'()'
            if ndim>=1:
                tmp8 =self.prefix_kernel_smc_endpointer+v+'=     '+self.prefix_kernel_smc_endpointer+tmp7+';\n'
                tmp8+=self.prefix_kernel_smc_startpointer+v+'=   '+self.prefix_kernel_smc_startpointer+tmp7+';\n'
            if ndim>=2:
                tmp8+=self.prefix_kernel_smc_endpointer+v+'_2d=  '+self.prefix_kernel_smc_endpointer+tmp7+'_2d;\n'
                tmp8+=self.prefix_kernel_smc_startpointer+v+'_2d='+self.prefix_kernel_smc_startpointer+tmp7+'_2d;\n'
            kernelB=kernelB.replace(tmp1,tmp1+'\n'+tmp8)
        else:
            datafetch+="\n // FINDING TILE START\n"
            datafetch+=    """/*
                               * This works as long as all threads of the thread block are active here.'
                               * Also works if threads from 0...Nx and 0...Ny
                               *   are active and Nx<blockDim.x Ny<blockDim.x'
                               * Generally might not work if threads are diverged here.
                               * For instance:
                               * might not work if threads from Lx...blockDim.x and Ly...blockDim.y
                               *    are active and Lx>0 or Ly>0
                               */\n"""
            # count the number threads active in this code region
            datafetch+="""/* Find the number of active threads in the thread block
                           * Configured by CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD in codegen.py
                           */\n"""
            if CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD==CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_SYNC:
                if ndim>=1:
                    datafetch+="int __ipmacc_stride_x = __syncthreads_count(threadIdx.y==0);\n"
                if ndim>=2:
                    datafetch+="int __ipmacc_stride_y = __syncthreads_count(threadIdx.x==0);\n"
            elif CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD==CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_ARG:
                if ndim>=1:
                    datafetch+='int __ipmacc_stride_x = (blockIdx.x==(gridDim.x-1))?__ipmacc_last_blockdim_x:blockDim.x;\n'
                if ndim>=2:
                    datafetch+='int __ipmacc_stride_y = (blockIdx.y==(gridDim.y-1))?__ipmacc_last_blockdim_y:blockDim.y;\n'
            elif CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD==CACHE_RBX_ACTIVE_THREADS_COUNT_METHOD_FIXED:
                if ndim>=1:
                    datafetch+='int __ipmacc_stride_x = blockDim.x;\n'
                if ndim>=2:
                    datafetch+='int __ipmacc_stride_y = blockDim.y;\n'
            else:
                print_error('cache: unknown thread count method', [])

            # find the subarray range shared within thread block
            datafetch+="""/* Find the pointers pointing to start and end of
                           * the subarray shared among threads of the thread block.
                           * Configured by CACHE_RBX_POINTER_TYPE in codegen.py
                           */\n"""
            if CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_COMMUN:
                if ndim==1:
                    datafetch+="if(threadIdx.x==0){\n"
                    datafetch+=self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+';\n'
                    datafetch+="}\n"
                    datafetch+="if(threadIdx.x==(__ipmacc_stride_x-1)){\n"
                    datafetch+=self.prefix_kernel_smc_endpointer+v+'  ='+p+'+'+up+';\n'
                    datafetch+="}\n"
                elif ndim==2:
                    datafetch+="if(threadIdx.x==0 && threadIdx.y==0){\n"
                    datafetch+=self.prefix_kernel_smc_startpointer+v+'   ='+p+'-'+dw+';\n'
                    datafetch+=self.prefix_kernel_smc_startpointer+v+'_2d='+pivot2+'-'+dw2range+';\n'
                    datafetch+="}\n"
                    datafetch+="if(threadIdx.x==(__ipmacc_stride_x-1) && threadIdx.y==(__ipmacc_stride_y-1)){\n"
                    datafetch+=self.prefix_kernel_smc_endpointer+v+'   ='+p+'+'+up+';\n'
                    datafetch+=self.prefix_kernel_smc_endpointer+v+'_2d='+pivot2+'+'+up2range+';\n'
                    datafetch+="}\n"
                else:
                    print_error('cache: unsupported multidimensional subarray!', [])
                datafetch+="__syncthreads();\n"
            elif CACHE_RBX_POINTER_TYPE==CACHE_RBX_POINTER_TYPE_PRIVATE:
                if ndim>=1:
                    if not f_is_stataic_p:
                        datafetch+=self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+'-threadIdx.y;\n'
                        datafetch+=self.prefix_kernel_smc_endpointer+v+'=blockDim.y+'+self.prefix_kernel_smc_startpointer+v+'+'+up+'+'+dw+'-1;\n'
                    else:
                        datafetch+=self.prefix_kernel_smc_startpointer+v+'='+p+'-'+dw+';\n'
                        datafetch+=self.prefix_kernel_smc_endpointer+v+'='+self.prefix_kernel_smc_startpointer+v+'+'+up+'+'+dw+';\n'
                if ndim>=2:
                    if not f_is_stataic_p2:
                        datafetch+=self.prefix_kernel_smc_startpointer+v+'_2d='+pivot2+'-'+dw2range+'-threadIdx.x;\n'
                        datafetch+=self.prefix_kernel_smc_endpointer+v+'_2d=blockDim.x+'+self.prefix_kernel_smc_startpointer+v+'_2d+'+up2range+'+'+dw2range+'-1;\n'
                    else:
                        datafetch+=self.prefix_kernel_smc_startpointer+v+'_2d='+pivot2+'-'+dw2range+';\n'
                        datafetch+=self.prefix_kernel_smc_endpointer+v+'_2d='+self.prefix_kernel_smc_startpointer+v+'_2d+'+up2range+'+'+dw2range+';\n'
            else:
                print_error('cache: unknown pointer calculation method!', [])

            datafetch+="// FINDING DONE\n"
            datafetch+='//__fusion_merge_boundary_'+str(len(fusionSMC)-1)+'()\n'
        return [datafetch, kernelB]

    # @ cache directive
    # set boundary pointers for RBC and RBI
    # input: int kernelId (ID of the current kernel)
    # input: string kernelB (kernel body)
    # input: string p (pivot index of 1st dim)
    # input: string v (cache subarray/variable name)
    # input: string up (#of elements before pivot that are cached on 1st dim)
    # input: string dw (#of elements after pivot that are cached on 1st dim)
    # input: string up2range (#of elements before pivot that are cached on 2nd dim)
    # input: string dw2range (#of elements after pivot that are cached on 2nd dim)
    # input: string ctadimx ((thread block size dim.x)
    # input: string ctadimy ((thread block size dim.y)
    # input: string t (v data type)
    # input: string dimlo (first dimension lower-bound of the array associated with the subarray)
    # input: string dimhigh (first dimension upper-bound of the array associated with the subarray)
    # input: string dim2low (second dimension lower-bound of the array associated with the subarray)
    # input: string dim2high (second dimension upper-bound of the array associated with the subarray)
    # input: bool isfusion (True if this subarray fetch can be merged with a previously generated code)
    # input: int fusionIdx (if isfusion, the fusion ID is returned in fusionSMC) 
    # input: bool f_is_stataic_p (True if p is static to induction variables, otherwise False)
    # input: bool f_is_stataic_p2 (True if pivot2 is static to induction variables, otherwise False)
    # input: bool subarrayndim (number of dimensions in subarray)
    # output: string of statments initializing the shared memory with data from subarray
    # output: string of new kernelB
    def oacc_smc_codegen_initial_fetch(self, kernelId, kernelB, p, pivot2, v, up, dw,\
            up2range, dw2range, ctadimx, ctadimy, t,\
            dimlo, dimhi, dim2low, dim2high,\
            isfusion, fusionIdx, fusionSMC,\
            f_is_stataic_p, f_is_stataic_p2, ndim):
        datafetch = ''
        if isfusion:
            # merge this fetch with previous one 
            tmp1='__fusion_merge_fetch_'+str(fusionIdx)+'()'
            if ndim==1:
                tmp2=self.prefix_kernel_smc_varpref+v+'[kk]='+v+'[idx];\n'
            elif ndim==2:
                tmp2=self.prefix_kernel_smc_varpref+v+'[kk][kk2]='+v+'[idx*'+dim2high+'+idx2];\n'
            else:
                print_error('cache: unsupported multidimensional subarray!', [])
            #print 'fusion! >'+str(fusionIdx)+'\n'+kernelB
            kernelB=kernelB.replace(tmp1,tmp1+'\n'+tmp2)
        else:
            if ndim==1:
                datafetch+='int __ipmacc_length='+self.prefix_kernel_smc_endpointer+v+'-'+self.prefix_kernel_smc_startpointer+v+'+1;\n'
                if GENDEBUGCODE:
                    datafetch+='assert((__ipmacc_length)<=(256+'+dw+'+'+up+'));\n' #FIXME
                datafetch+='int kk=0;\n'
                if dw.strip()=='0' and up.strip()=='0':
                    datafetch+="kk=threadIdx.x;\n";
                else:
                    datafetch+='for(int kk=threadIdx.x; kk<__ipmacc_length; kk+=__ipmacc_stride_x)\n'
                datafetch+='{\n'
                datafetch+='int idx='+self.prefix_kernel_smc_startpointer+v+'+kk;\n'
                datafetch+='if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
                datafetch+='{\n'
                datafetch+=self.prefix_kernel_smc_varpref+v+'[kk]='+v+'[idx];\n'
                datafetch+='//'+self.prefix_kernel_smc_tagpref+v+'[kk]=1;\n'
                datafetch+='}\n'
                datafetch+='}\n'
                datafetch+='__syncthreads();\n'
                datafetch+='} // end of fetch\n'
                # pragma to replace global memory access with smc 
                # kernelB=kernelB.replace(fcall,datafetch+'\n'+fcall)
            elif ndim==2:
                datafetch+='int __ipmacc_length='+self.prefix_kernel_smc_endpointer+v+'-'+self.prefix_kernel_smc_startpointer+v+'+1;\n'
                datafetch+='int __ipmacc_length_2d='+self.prefix_kernel_smc_endpointer+v+'_2d-'+self.prefix_kernel_smc_startpointer+v+'_2d+1;\n'
                if GENDEBUGCODE:
                    datafetch+='assert((__ipmacc_length)<=(256+'+dw+'+'+up+'));\n' #FIXME
                codeblock_4_0='int kk=0,kk2=0;\n'
                codeblock_4_1='  kk2=threadIdx.x;\n'
                codeblock_4_2='  for(kk2=threadIdx.x; kk2<__ipmacc_length_2d; kk2+=__ipmacc_stride_x)\n'
                codeblock_4 = codeblock_4_0
                if (dw.strip()=='0' and up.strip()=='0') or str(eval(dw.strip()+'+'+up.strip()+'+1'))==ctadimx:
                    codeblock_4 += codeblock_4_1
                else:
                    codeblock_4 += codeblock_4_2
                codeblock_5="""
                          {
                           int idx2="""+self.prefix_kernel_smc_startpointer+v+"""_2d+kk2;
                           if(idx2<("""+dim2high+""") && idx2>=("""+dim2low+"""))
                           {
                            """
                codeblock_6_1='  kk=threadIdx.y;\n'
                codeblock_6_2='for(kk=threadIdx.y; kk<__ipmacc_length; kk+=__ipmacc_stride_y)\n'
                if (dw2range.strip()=='0' and up2range.strip()=='0') or str(eval(dw2range.strip()+'+'+up2range.strip()+'+1'))==ctadimy:
                    codeblock_6 = codeblock_6_1
                else:
                    codeblock_6 = codeblock_6_1
                codeblock_7="""
                     {
                      int idx="""+self.prefix_kernel_smc_startpointer+v+"""+kk;
                      if(idx<("""+dimhi+""") && idx>=("""+dimlo+"""))
                     {
                    """
                codeblock_8=''
                codeblock_8+=self.prefix_kernel_smc_varpref+v+'[kk][kk2]='+v+'[idx*'+dim2high+'+idx2];\n'
                codeblock_8+='//__fusion_merge_fetch_'+str(len(fusionSMC)-1)+'()\n'
                codeblock_8+='   }\n'
                codeblock_8+='  }\n'
                codeblock_8+=' }\n'
                codeblock_8+='}\n'

                # datafetch+= 'if(__ipmacc_stride_x==blockDim.x && __ipmacc_stride_y==blockDim.y){\n'
                datafetch+= 'if(__ipmacc_stride_x>=__ipmacc_length_2d && __ipmacc_stride_y>=__ipmacc_length){\n'
                datafetch+= codeblock_4+codeblock_5+codeblock_6+codeblock_7+codeblock_8
                datafetch+= '\n}else{\n'
                datafetch+= codeblock_4_0+codeblock_4_2+codeblock_5+codeblock_6_2+codeblock_7+codeblock_8
                datafetch+= '}\n'
                datafetch+='__syncthreads();\n'
                # kernelB=kernelB.replace(fcall,datafetch+'\n'+fcall)
            else:
                print_error('cache: unsupported multidimensional subarray!', [])

        return [datafetch, kernelB]

    # @ cache directive
    # set boundary pointers for RBC and RBI
    # input: string v (cache subarray/variable name)
    # input: string a ()
    # input: string t (v data type)
    # input: string length   (length of 1st dimension of cache allocated in shared memory)
    # input: string length_2 (length of 2nd dimension of cache allocated in shared memory)
    # input: string div (false if RBI, false if RBC)
    # output: string of statements declaring cache read routine
    # output: string of statements declaring cache write routine
    def oacc_smc_codegen_readwrite_calls(self, t, a, v, length, length_2, div):
        # construct the smc_select_ per array for READ
        smc_select_calls ='__forceinline__ __device__ '+t.replace('*','')+' __smc_select_'+str(a)+'_'+v+'(int index1, int index2,\n'
        #smc_select_calls+=((tagbasedcache_datp+' tag_array['+tagbasedcache_size+'], ') if tagbasedcache_size!='' else '')+'\n'
        smc_select_calls+=t+' g_array, '
        #smc_select_calls+=t.replace('*','')+(' s_array['+tagbasedcache_size+'], ' if tagbasedcache_size!='' else ' s_array['+length+']['+length_2+'], ')+'\n'
        smc_select_calls+=t.replace('*','')+(' s_array['+length+']['+length_2+'], ')+'\n'
        smc_select_calls+=' int startptr1, int startptr2, int endptr1, int endptr2, int pitch, int diff1, int diff2){\n'
        if div=='false':
            smc_select_calls+='// the pragmas are well-set. do not check the boundaries.\n'
            # if GENDEBUGCODE:
            #     smc_select_calls+="""#define REPLACECALL() printf("tid> (%d,%d,%d) bid> (%d,%d,%d) index> %d idx> %d idx2> %d startptr> %d startptr2> %d\\n",\\
            #     threadIdx.x,threadIdx.y,threadIdx.z,\\
            #     blockIdx.x,blockIdx.y,blockIdx.z,\\
            #     index,idx,idx2,startptr,startptr2);\n
            # if(!(((idx-startptr)>=0))){\n
            #     REPLACECALL()\n
            #         assert((idx-startptr)>=0);\n
            # }\n
            # if(!((idx-startptr)<("""+length+"""))){\n
            #     REPLACECALL()\n
            #         assert((idx-startptr)<("""+length+"""));\n
            # }\n
            # if(!((idx2-startptr2)>=0)){\n
            #     REPLACECALL()\n
            #         assert((idx2-startptr2)>=0);\n
            # }\n
            # if(!((idx2-startptr2)<("""+length_2+"""))){\n
            #     REPLACECALL()\n
            #         assert((idx2-startptr2)<"""+length_2+""");\n
            # }\n"""
            smc_select_calls+='return s_array[index1-startptr1][index2-startptr2];\n'
        else:
            #print 'Warning! divergent is not implemented for 2D SMC. Falling back to non-divergent'
            smc_select_calls+='// the pragmas are not well-set. do check the boundaries.\n'
            smc_select_calls+='// also we check the tag to assure data is already fetched.\n'
            # if GENDEBUGCODE:
            #     smc_select_calls+="""#define REPLACECALL() printf("tid> (%d,%d,%d) bid> (%d,%d,%d) index> %d idx> %d idx2> %d startptr> %d startptr2> %d\\n",\\\n
            #     threadIdx.x,threadIdx.y,threadIdx.z,\\\n
            #     blockIdx.x,blockIdx.y,blockIdx.z,\\\n
            #     index,idx,idx2,startptr,startptr2);\n
            # if(!(((idx-startptr)>=0))){\n
            #     REPLACECALL()\n
            #         assert((idx-startptr)>=0);\n
            # }\n
            # if(!((idx-startptr)<16)){\n
            #     REPLACECALL()\n
            #         assert((idx-startptr)<16);\n
            # }\n
            # if(!((idx2-startptr2)>=0)){\n
            #     REPLACECALL()\n
            #         assert((idx2-startptr2)>=0);\n
            # }\n
            # if(!((idx2-startptr2)<20)){\n
            #     REPLACECALL()\n
            #         assert((idx2-startptr2)<16);\n
            # }\n"""
            #smc_select_calls+='return s_array[diff1][diff2];\n'
            # if tagbasedcache_size!='':
            #     smc_select_calls+=t.replace('*','')+' value_to_return;\n'
            #     smc_select_calls+='int gidx = (index1*pitch+index2);\n'
            #     smc_select_calls+='//return g_array[gidx];\n'
            #     smc_select_calls+='int sidx = (gidx)&('+tagbasedcache_size+'-1);\n'
            #     smc_select_calls+='if(tag_array[sidx]==(gidx)){\n'
            #     smc_select_calls+='value_to_return = s_array[sidx];\n'
            #     smc_select_calls+='}\n'
            #     smc_select_calls+='bool tag_updated=false;\n'
            #     smc_select_calls+='if(tag_array[sidx]!=(gidx)){ \n'
            #     smc_select_calls+='value_to_return = g_array[gidx];\n'
            #     smc_select_calls+='s_array[sidx] = value_to_return;\n'
            #     smc_select_calls+='tag_updated = true;\n'
            #     smc_select_calls+='}\n'
            #     smc_select_calls+='__syncthreads();\n' 
            #     smc_select_calls+='if(tag_updated) tag_array[sidx] = gidx;\n' 
            #     smc_select_calls+='__syncthreads();\n' 
            #     smc_select_calls+='return value_to_return;\n'
            # else:
            #     smc_select_calls+=t.replace('*','')+' ret = s_array[diff1][diff2];\n'
            #     smc_select_calls+='if(!(index1>=startptr1 && index1<=endptr1 && index2>=startptr2 && index2<=endptr2 )){\n'
            #     #smc_select_calls+='assert(0);\n'
            #     smc_select_calls+='ret = g_array[index1*pitch+index2];\n'
            #     smc_select_calls+='}\n'
            #     smc_select_calls+='return ret;\n'
            smc_select_calls+=t.replace('*','')+' ret = s_array[diff1][diff2];\n'
            smc_select_calls+='if(!(index1>=startptr1 && index1<=endptr1 && index2>=startptr2 && index2<=endptr2 )){\n'
            smc_select_calls+='ret = g_array[index1*pitch+index2];\n'
            smc_select_calls+='}\n'
            smc_select_calls+='return ret;\n'

        smc_select_calls+='}\n'
        # smc_write_calls+='__device__ void __smc_write_'+str(a)+'_'+v+'(int index1, int index2, '+\
        #     ((tagbasedcache_datp+' tag_array['+tagbasedcache_size+'], ') if tagbasedcache_size!='' else '')+\
        #     t+' g_array, '+t.replace('*','')+\
        #     (' s_array['+tagbasedcache_size+'],' if tagbasedcache_size!='' else ' s_array['+length+']['+length_2+'], ')+\
        #     ' int startptr1, int startptr2, int endptr1, int endptr2, int pitch, '+\
        #     t.replace('*','')+' value){\n'
        smc_write_calls ='__device__ void __smc_write_'+str(a)+'_'+v+'(int index1, int index2, '+\
            t+' g_array, '+t.replace('*','')+\
            ' s_array['+length+']['+length_2+'], '+\
            ' int startptr1, int startptr2, int endptr1, int endptr2, int pitch, '+\
            t.replace('*','')+' value){\n'
        if div=='false':
            smc_write_calls+='// the pragmas are well-set. do not check the boundaries.\n'
            smc_write_calls+='s_array[index1-startptr1][index2-startptr2]=value;\n'
        else:
            #print 'Warning! divergent is not implemented for 2D SMC. Falling back to non-divergent'
            # if tagbasedcache_size:
            #     smc_write_calls+='int gidx = (index1*pitch+index2);\n'
            #     smc_write_calls+='int sidx = (gidx)&('+tagbasedcache_size+'-1);\n'
            #     smc_write_calls+='if(tag_array[sidx]==(gidx)){\n'
            #     smc_write_calls+='s_array[sidx]=value;\n'
            #     smc_write_calls+='}else{ \n'
            #     smc_write_calls+='g_array[tag_array[sidx]]=s_array[sidx];\n'
            #     smc_write_calls+='s_array[sidx] = g_array[gidx];\n'
            #     smc_write_calls+='tag_array[sidx]=gidx;\n'
            #     smc_write_calls+='//__syncthreads();\n' 
            #     smc_write_calls+='}\n'
            # else:
            #     smc_write_calls+='if(index1>=startptr1 && index1<=endptr1 && index2>=startptr2 && index2<=endptr2){\n'
            #     smc_write_calls+='s_array[index1-startptr1][index2-startptr2]=value;\n'
            #     smc_write_calls+='}else{\n'
            #     smc_write_calls+='g_array[index1*pitch+index2]=value;\n'
            #     smc_write_calls+='}\n'
            smc_write_calls+='if(index1>=startptr1 && index1<=endptr1 && index2>=startptr2 && index2<=endptr2){\n'
            smc_write_calls+='s_array[index1-startptr1][index2-startptr2]=value;\n'
            smc_write_calls+='}else{\n'
            smc_write_calls+='g_array[index1*pitch+index2]=value;\n'
            smc_write_calls+='}\n'

        smc_write_calls+='}\n'
        return [smc_select_calls, smc_write_calls]
    
    def oacc_smc_codegen_cache_region_replace_accesses(self, a, v, t,\
            p, dw, up,\
            pivot2, dw2range, up2range,\
            dim2high, div, fcall,\
            kernelB, st):
        fcallst=self.prefix_kernel_smc_fetch+str(a)+'();'
        fcallen=self.prefix_kernel_smc_fetchend+str(a)+'();'
        changeRangeIdx_start=kernelB.find(fcallst)
        changeRangeIdx_end=kernelB.find(fcallen)
        #print kernelB[changeRangeIdx_start:changeRangeIdx_end]
        if (changeRangeIdx_start==-1 ) or (changeRangeIdx_end==-1) or (changeRangeIdx_start>changeRangeIdx_end):
            print 'fatal error! could not determine the smc range for '+v
            exit(-1)
        # READ WRITE REPLACE ACCESSES
        [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet] = self.smc_kernelBody_parse(kernelB, changeRangeIdx_start, changeRangeIdx_end, a, v, st, dim2high, p, dw, up)
        for idx_num in range(len(readIdxStartEndPtrs)-1, -1, -1):
            [idx_s, idx_e]=readIdxStartEndPtrs[idx_num]
            if DEBUGSMCPRECALCINDEX:
                print '> '+kernelB[idx_s:idx_e]
            if div=='false':
                kernelB=kernelB[:idx_s]+self.prefix_kernel_smc_varpref+v+'['+'__ipmacc_smc_index_'+v+'_'+str(readIdxList[idx_num])+'_dim1'+']['+'__ipmacc_smc_index_'+v+'_'+str(readIdxList[idx_num])+'_dim2'+']'+' /* replacing '+kernelB[idx_s:idx_e]+'*/ '+kernelB[idx_e:]
            else:
                [tmp_idx1, tmp_idx2] = self.decompose1Dindexto2D(unifiedIdxSet[unifiedIdxList[idx_num]], '0', dim2high, '2D')
                tmp_diff1=tmp_idx1+'-'+self.prefix_kernel_smc_startpointer+v
                tmp_diff2=tmp_idx2+'-'+self.prefix_kernel_smc_startpointer+v+'_2d'
                    #(self.prefix_kernel_smc_tagpref+v+', ' if tagbasedcache_size else '')+v+', '+
                access_tmp='__smc_select_'+str(a)+'_'+v+'('+tmp_idx1+', '+tmp_idx2+', '+\
                    v+', '+\
                    self.prefix_kernel_smc_varpref+v+', '+self.prefix_kernel_smc_startpointer+v+', '+\
                    self.prefix_kernel_smc_startpointer+v+'_2d'+', '+self.prefix_kernel_smc_endpointer+v+', '+\
                    self.prefix_kernel_smc_endpointer+v+'_2d'+', '+dim2high+','+tmp_diff1+','+tmp_diff2+')'
                kernelB=kernelB[:idx_s]+access_tmp+'/* '+kernelB[idx_s:idx_e]+'*/ '+kernelB[idx_e:]
        indexCalculationCode=self.smc_get_indexCalculation(readIdxSet, readIdxList, v, dim2high, writeIdxSet, writeIdxList, unifiedIdxSet, unifiedIdxList, '2D')
        kernelB=kernelB.replace(fcall,indexCalculationCode+fcall)
        changeRangeIdx_start=kernelB.find(fcallst)
        changeRangeIdx_end=kernelB.find(fcallen)
        [writeIdxList, readIdxList, readIdxSet, readIdxStartEndPtrs, writeIdxSet, writeIdxStartEndPtrs, unifiedIdxList, unifiedIdxSet] = self.smc_kernelBody_parse(kernelB, changeRangeIdx_start, changeRangeIdx_end, a, v, st, dim2high, p, dw, up)
        # list all read accesses
        # unpack and replace write-accesses
        for wi in range(len(writeIdxStartEndPtrs)-1,-1,-1):
            [v, a, p, dw, up, wst, wen, asgidx]=writeIdxStartEndPtrs[wi]
            writeIdx_loc=']'.join('['.join(kernelB[wst:asgidx].split('[')[1:]).split(']')[:-1])
            writeIdx_val=kernelB[asgidx+1:wen]
            writeIdx_replacer ='__syncthreads();\n'
            if div=='false':
                writeIdx_replacer+=self.prefix_kernel_smc_varpref+v+'['+'__ipmacc_smc_index_'+v+'_'+str(writeIdxList[wi])+'_dim1'+']['+'__ipmacc_smc_index_'+v+'_'+str(writeIdxList[wi])+'_dim2'+']='+writeIdx_val[:-1]+';\n'
            else:
                print 'cache divergent write not implemented! #'+str(getframeinfo(currentframe()).lineno)+'\n'
                exit(-1)
                if TAGBASEDSMC:
                    writeIdx_replacer+='__smc_write_'+str(a)+'_'+v+'('+tmp_idx1+', '+tmp_idx2+', '+(self.prefix_kernel_smc_tagpref+v+', ' if TAGBASEDSMC else '')+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_startpointer+v+'_2d'+', '+self.prefix_kernel_smc_endpointer+v+', '+self.prefix_kernel_smc_endpointer+v+'_2d'+', '+dim2high+','+writeIdx_val[:-1]+')'
                else:
                    writeIdx_replacer+='__smc_write_'+str(a)+'_'+v+'('+tmp_idx1+', '+tmp_idx2+', '+(self.prefix_kernel_smc_tagpref+v+', ' if TAGBASEDSMC else '')+v+', '+self.prefix_kernel_smc_varpref+v+', '+self.prefix_kernel_smc_startpointer+v+', '+self.prefix_kernel_smc_startpointer+v+'_2d'+', '+self.prefix_kernel_smc_endpointer+v+', '+self.prefix_kernel_smc_endpointer+v+'_2d'+', '+dim2high+','+tmp_diff1+','+tmp_diff2+')'
            writeIdx_replacer+='__syncthreads();\n'
            kernelB=kernelB[0:wst]+writeIdx_replacer+kernelB[wen+1:]
        return [fcallen, kernelB]

    def oacc_smc_codegen_writeback(self, length, length_2, w_dw, w_up,\
            w_dw2range, w_up2range, v, dimlo, dimhi, dim2low, dim2high, fcallen):
        # fetch data to local memory
        writeback ='{ // writeback begins\n'
        writeback+='__syncthreads();\n'
        if w_dw=='':
            wlength=length
        else:
            wlength=self.blockDim_cuda_xyz+'+'+w_dw+'+'+w_up
        if w_dw2range=='':
            wlength_2=length_2
        else:
            wlength_2=self.blockDim_cuda_xyz+'+'+w_dw2range+'+'+w_up2range
        writeback+='int kk=0,kk2=0;\n'
        writeback+='int rw_offset = '+dw+'-'+w_dw+';\n'
        writeback+='int rw_offset_2 = '+dw2range+'-'+w_dw2range+';\n'
        writeback+='int  __ipmacc_stride=__syncthreads_count(1);\n'
        writeback+='for(kk=0; kk<('+wlength+'); kk++)\n'
        #writeback+='for(int kk=threadIdx.x; kk<('+wlength+'); kk+=__ipmacc_stride)\n'
        writeback+='{\n'
        writeback+=' int idx='+self.prefix_kernel_smc_startpointer+v+'+kk+rw_offset;\n'
        writeback+=' if(idx<('+dimhi+') && idx>=('+dimlo+'))\n'
        writeback+=' {\n'
        writeback+='  for(kk2=threadIdx.y*blockDim.x+threadIdx.x; kk2<('+wlength_2+'); kk2+=__ipmacc_stride)\n'
        writeback+='  {\n'
        writeback+='   int idx2='+self.prefix_kernel_smc_startpointer+v+'_2d+kk2+rw_offset_2;\n'
        writeback+='   if(idx2<('+dim2high+') && idx2>=('+dim2low+'))\n'
        writeback+='   {\n'
        writeback+=v+'[idx*'+dim2high+'+idx2]='+self.prefix_kernel_smc_varpref+v+'[kk+rw_offset][kk2+rw_offset_2];\n'
        writeback+='   }\n'
        writeback+='  }\n'
        writeback+=' }\n'
        writeback+='}\n'
        writeback+='__syncthreads();\n'
        writeback+='} // end of writeback\n' 
        kernelB=kernelB.replace(fcallen,writeback+'\n'+fcallen)
        return kernelB


    # @ cache directive
    # determine the size of subarray in the cache for a thread block
    # input: string ctadimx (size of this dimension of thread block)
    # input: string up (subarray elements after pivot)
    # input: string dw (subarray elements before pivot)
    # input: bool flag (True if pivot is static to kernel's induction variables, otherwise False)
    # input: string pivot (subarray pivot index)
    # output: string of cache size
    def oacc_smc_squeez_size(self, ctadimx, up, dw, flag, pivot, loop_induction_vars_list, code):
        [rate, offset] = self.smc_cache_base_normal_get_RO(pivot, loop_induction_vars_list, code)
        if flag:
            if   ctadimx==str(eval(up+'+1')):
                length  =rate+'*'+ctadimx+('' if dw=='0' else '+'+dw)
            elif ctadimx==str(eval(dw+'+1')):
                length  =rate+'*'+ctadimx+('' if up=='0' else '+'+up)
            else:
                length  =rate+'*'+ctadimx+('' if dw=='0' else '+'+dw)+('' if up=='0' else '+'+up)
        else:
            length  =rate+'*'+ctadimx+('' if dw=='0' else '+'+dw)+('' if up=='0' else '+'+up)
        # print 'squeezed to > ', length, flag, rate, ctadimx #FIXME
        return length

    def oacc_smc_get_endpointer(self, flag, p, up, ctadimx):
        if flag:
            if   ctadimx==up:
                length  =p+'+'+ctadimx+'-1'
            else:
                length  =p+'+'+ctadimx+('' if up=='0' else '+'+up)
        else:
            length  =p+'+'+ctadimx+('' if up=='0' else '+'+up)
        return length
    def recursive_compVar_tracer(self,fname,compArgsInd):
        for i in range(0,len(self.active_calls_decl)):
            if self.active_calls_decl[i][0]==fname:
                curFuncInd=i
                m=re.search(fname+'\s*\((.*?)\)',self.active_calls_decl[i][2],re.S)
                #print m.group(1)
                argList = m.group(1).split(',')
                for argIndex in compArgsInd:
                    self.func_comp_vars[fname].append([argList[argIndex[0]].replace('*',' ').strip().split()[-1],argIndex[1]])
                break
        for fCall in self.active_calls_decl:
            if self.active_calls_decl[curFuncInd][2].find(fCall[0])!=-1 and self.active_calls_decl[curFuncInd][0]!=fCall[0]:
                funcCompArgList=[]
                m=re.search(fCall[0]+'\s*\((.*?)\)',self.active_calls_decl[curFuncInd][2],re.S)#assume there's no parentheses in function arguments
                argList = m.group(1).split(',')
                for compVar in self.func_comp_vars[fname]:
                    for arg in argList:
                       # print arg.strip()
                        if compVar[0] == arg.strip():
                            funcCompArgList.append([argList.index(arg),compVar[1]])
#                            argList.append("__conpress_constant_"+compVar[0])
#                self.active_calls_decl[curFuncInd][2]=self.active_calls_decl[curFuncInd][2].replace(m.group(0),fCall[0]+'_compression('+','.join(argList)+')')
                self.recursive_compVar_tracer(fCall[0],funcCompArgList)
    def generate_code(self):
        Argus=[]
        KBody=[]
        Decls=[]
        FDims=[]
        Privs=[]
        Redus=[]
        Smcis=[]
        CTADIMs=[]
        CompList=[]
        for i in range(0,len(self.oacc_kernels)):
            if DEBUGLD:
                print 'finding the kernel dimension (`for` size)...'
            self.oacc_extra_symbols.append([])
            [iterators_p, purestring, iterators_s]=self.find_kernel_forSize(self.oacc_kernels[i])
            #print 'it could be something like -> '+str(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
            #print 'it could be something like -> '+self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
            if DEBUGLD or DEBUGVAR:
                 print 'iterators  of parallel   loops :'+','.join(iterators_p)
                 print 'undeclared iterators  of sequential loops :'+','.join(iterators_s)
            iterators_p = list(set(iterators_p))
            self.oacc_kernelsLoopIteratorsPar.append(iterators_p)
            self.oacc_kernelsLoopIteratorsSeq.append(iterators_s)
            algorithm_ranks = []
            self.label_for_depth(self.oacc_kernels[i],algorithm_ranks)
            forDims=self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i], algorithm_ranks))
            kernelBody=self.var_kernel_genPlainCode(i, self.oacc_kernels[i], 0)
            [nctadim, ctadimx, ctadimy, ctadimz]=self.oacc_kernelsConfig_getDecl(i)
            if (nctadim>1 or GENMULTIDIMTB):
                # return a list of loop dimensions mapped to different grid dimensions 
                # assigns details to loops
                ##self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))
                # finding loop dimension 
                forDims=[]
                # up to three nested loops
                matrix_of_for_loops = []
                self.kernel_forSize_list_matrix(self.oacc_kernels[i], 1, i, matrix_of_for_loops)
                #print matrix_of_for_loops
                #exit(-1)
                #for nest in range(nctadim-1, 0-1, -1):
                #    forDims.append(self.kernel_forSize_list(self.oacc_kernels[i], nest, 0, i))
                for dimm in matrix_of_for_loops[::-1]:
                    isalgo=False
                    algowidth=''
                    for [source, vector] in dimm:
                        if source=='a':
                            isalgo = True
                            algowidth = vector
                    if isalgo:
                        # proceed with desired width from algorithm directive
                        forDims.append(algowidth)
                    else: 
                        # calculate the maximum 
                        if len(dimm)>1:
                            forDims.append('IPMACC_MAX'+str(len(dimm))+'('+','.join([v for [s, v] in dimm])+')')
                        else:
                            forDims.append('('+','.join([v for [s, v] in dimm])+')')
                # print len(forDims)
                if DEBUGMULTIDIMTB:
                    print ','.join(forDims)
                    #exit(-1)
            #else:
                # assigns details to loops
                # finding loop dimension 
                #forDims=self.kernel_forSize_CReadable(self.find_kernel_forSize_Recursive(self.oacc_kernels[i]))

            if DEBUGLD and not GENMULTIDIMTB:
                print 'total concurrent threads -> '+forDims
            #print 'assigning copy details'
            [args, declaration, implicitCopies, privInfo, reduInfo, smcInfo]=self.find_kernel_undeclaredVars_and_args(kernelBody, i)
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
            Smcis.append(smcInfo)
            CTADIMs.append([nctadim, ctadimx, ctadimy, ctadimz])
            compInfo=self.oacc_kernelsComp[i]
            CompList.append(compInfo)
        
        # here we have resolved all the functions called within all kernels regions
        # now we look for the functions
        self.implant_function_prototypes()
        self.forward_declare_find()
        # append global arrays to implicit copies
        self.inflate_kernels_for_global_vars(KBody, Argus)
        #self.var_copy_showAll()

        self.var_copy_assignExpDetail(FDims, (self.blockDim_cuda if self.target_platform=='CUDA' else self.blockDim_opencl))
        self.var_copy_genCode()
        #k.var_copy_showAll()
        #k.varmapper_showAll()

        for i in range(0,len(self.oacc_kernels)):
            # carry the loop break
            args=        Argus[i]
            kernelBody=  KBody[i]
            declaration= Decls[i]
            forDims=     FDims[i]
            privInfo=    Privs[i]
            reduInfo=    Redus[i]
            smcInfo=     Smcis[i]
            ctasize=     CTADIMs[i]
            compInfo= CompList[i]
            if DEBUGPRIVRED:
                self.debug_dump_privredInfo('private',privInfo)
                self.debug_dump_privredInfo('reduction',reduInfo)
            # loop continue
            [kernelPrototype, kernelDecl]=self.codegen_constructKernel(args, declaration, kernelBody, i, privInfo, reduInfo, ctasize, forDims, smcInfo, compInfo)
            #[kernelPrototype, kernelDecl]=self.codegen_constructKernel(args, declaration, kernelBody, i, privInfo, reduInfo, (self.blockDim_cuda if self.target_platform=='CUDA' else self.blockDim_opencl), forDims, smcInfo)
            # FIXME COMPRESSION
            self.codegen_appendKernelToCode(kernelPrototype, kernelDecl, i, forDims, args, smcInfo)
            for fCall in self.active_calls_decl:
                if kernelDecl.find(fCall[0])!=-1:
                    funcCompArgList=[]
                    m=re.search(fCall[0]+'\((.*?)\)',kernelDecl,re.S)
                    argList = m.group(1).split(',')
                    for compVarObj in self.oacc_kernelsComp[i]:
                        #print compVar 
                        #print fCall[0]
                        for arg in argList:
                            #print arg.strip()
                            if compVarObj.varName == arg.strip():
                                funcCompArgList.append([argList.index(arg),compVarObj.varName])
                        #print funcCompArgList  
#                    kernelDecl=kernelDecl.replace(m.group(0),'__accelerator_'+fCall[0]+'('+','.join(argList)+')')
                    self.recursive_compVar_tracer(fCall[0],funcCompArgList)
            if DEBUGCOMPRESSION:
                print self.func_comp_vars



        if self.target_platform=='OPENCL':
            for k in range(0,len(self.code_kernels)):
                self.code=self.code.replace(self.prefix_kernel+str(k)+'();',self.code_kernels[k])
            #self.codegen_renameStadardTypes()
            self.codegen_renameStadardCalls()
        if self.target_platform=='CUDA':
            if len(self.oacc_kernelsComp)>0:
                #print self.oacc_kernelsComp
                self.code+="__device__ __inline unsigned short compress_float(float fNum, float* coef){\n\
                 float temp;\n\
                 temp = fNum*coef[2]+1.5;\n\
                 return (unsigned short)(((*((unsigned int*)&temp))>>7)&0x0000FFFF);\n}\n"
                self.code+="__device__ __inline unsigned short compress_double(double dNum, double* coef){\n\
                 double temp;\n\
                 temp = dNum*coef[2]+1.5;\n\
                 return (unsigned int)(((*((unsigned long long*)&temp))>>20)&0x00000000FFFFFFFF);\n}\n"
                self.code+="__device__ __inline float decompress_float(void *ptr,int index,float* coef){\n\
                 unsigned int temp;\n\
                 temp=((unsigned short*)ptr)[index];\n\
                 temp=temp<<7;\n\
                 return ((*((float*)&(temp=temp | 0x3F800000))*coef[0]+coef[1]));\n}\n"
                self.code+="__device__ __inline double decompress_double_CR4(void *ptr,int index,double* coef){\n\
                 unsigned long long temp;\n\
                 temp=((unsigned short*)ptr)[index];\n\
                 temp=temp<<(20+16);\n\
                 return (*((double*)&(temp=temp | 0x3FF0000000080000))*coef[0]+coef[1]);\n}\n"
                self.code+="__device__ __inline double decompress_double(void *ptr,int index,double* coef){\n\
                 unsigned long long temp;\n\
                 temp=((unsigned int*)ptr)[index];\n\
                 temp=temp<<20;\n\
                 return (*((double*)&(temp=temp | 0x3FF0000000080000))*coef[0]+coef[1]);\n}\n"
            # we can make OpenCL to follow this, however, separating them is easier to debug final code
            #self.code =self.codegen_getFuncProto()  +self.cuda_kernelproto+self.code
            #self.code =self.codegen_getTypeFwrDecl()+self.code
            self.active_calls_decl +=self.cuda_sort_get_func()
            self.code+=self.codegen_getFuncDecls()  +self.cuda_kerneldecl
            #self.codegen_renameStadardTypes()
        if self.target_platform=='ISPC':
            self.ispc_kerneldecl += self.codegen_getFuncDecls() 
            self.generate_kernel_file_ispc()


# check for codegen options
parser = OptionParser()
parser.add_option("-f", "--file", dest="filename",
                  help="Path to output CU file", metavar="FILE", default="")
parser.add_option("-t", "--targetarch", dest="target_platform",
                  help="Target code (nvcuda, nvopencl, or intelispc)", default="")
parser.add_option("-a", "--args", dest="nvcc_args",
                  help="Arguments passed to code generator (mostly, to communicate with underlying gnu cpp)", default="")
parser.add_option("-o", "--opt", dest="optimizations",
                  help="Enabled optimizations (availables are: readonlycache)", default="")
parser.add_option("-p", "--perforation-config", dest="perforationconf",
                  help="Enabled optimizations (availables are: readonlycache)", default="")
(options, args) = parser.parse_args()

if options.target_platform=="":
    parser.print_help()
    exit(-1)

if options.filename=="":
    parser.print_help()
    exit(-1)
else:
    print '  warning: storing the translated code in <'+options.filename+'> (target: <'+options.target_platform+'>)'


# read the input XML which is validated by parser
tree = ET.parse('__inter.xml')
root = tree.getroot()
if CLEARXML:
    os.remove('__inter.xml')

# create a code generator module
k = codegen(options.target_platform, options.filename, options.nvcc_args, options.optimizations, options.perforationconf)

# prepare the destination code by parsing the XML tree
k.code_descendentRetrieve(root,0,[])

if True or k.acc_detected():
    if not CLEARXML:
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
    if DEBUGSTMBRK:
        print k.code
        for [typ,stm] in k.code_getAssignments(k.code,['def','inc','typ','str']):
            print typ+' : '+stm[0:40].replace('\n',' ').strip()+'...'
    k.generate_code()
    k.codegen_includeHeaders()
else:
    print 'warning: no OpenACC kernel region is detected.'


# prepare to write the code to output
k.code_descendentDump(options.filename)

if VERBOSE:
    print "code geneneration completed!"

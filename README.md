IPMACC is originally developed at Institute for Research in Fundamental Sciences (IPM), Tehran, Iran. The framework includes set of translators to execute OpenACC for C applications over CUDA or OpenCL runtime. First, the framework translates OpenACC for C API to CUDA and OpenCL. Then, it compiles the CUDA/OpenCL code with the system compiler allowing the execution of application over CUDA or OpenCL -capable devices.

IPMACC supports data, kernels, loop, enter, and exit directives. It also allows user-defiend data types and function calls within accelerator regions. We believe IPMACC is more of translator than a compiler, outputing the CUDA/OpenCL code which is equivalent to the input OpenACC code. It allows further optimization by CUDA developer. Also IPMACC can be used as a framework for extending OpenACC framework and evaluating new directive/clauses. Please refer to Limitation section of this document to overview supported directives and API calls.

# Getting Started:
* Refer to docs/ipmacc-openacc.pptx to learn basics of OpenACC.
* Refer to INSTALL file for performing the installation.
* Refer to docs/ipmacc-performance.pdf to see the performance comparison of OpenACC applications compiled by our implementation to native CUDA implementation.
* After the installation, the best way to start is to compile and run the samples in the test-case/ directory. Example:
```
    $ ipmacc test-case/vectorAdd.c -o vectorAdd
    $ ./vectorAdd
```
* There are microbenchmarks to evaluate the overhead of memory allocation, memory copies, and kernel launches under test-case/microbenchmarks/ directory. Also there are wide set of benchmarks under test-case/rodinia/


# Usage:
* IPMACC is a command-line tool reading single source and generating the destination CUDA/OpenCL source (and also the object or binary). It has few limited compile switch. See the available switches with the following commands:

`$ ipmacc --help`

* In a case that there is a switch which IPMACC does not understands, IPMACC passes the switch to the system compiler. Hence, technically, IPMACC accepts all switches of the system compiler. The system compiler is `nvcc` in case of CUDA target and `gcc` in case of OpenCL target. Examples:
    * In case of CUDA backend, which is the default, the following command generates a binary for Kepler GPUs:
      `$ ipmacc acc_source.cpp -arch=sm_35 -o binary`

# Runtime environment variables:
* Set **IPMACC_VERBOSE** to run the code in verbose mode debuggin your code with the generate code (copies, kernel launches, and
    synchronizations):

    `$ export IPMACC_VERBOSE=1`

* Set **IPMACCLIB_VERBOSE** to run the code in verbose mode debuggin IPMACC OpenACC underlying library:

    `$ export IPMACCLIB_VERBOSE=1`

# IPMACC Extensions to OpenACC
Refer to EXTENSIONS file to read about the IPMACC additions.

# Limitations:
Current version of IPMACC has several limitations in fully implementing OpenACC standard:
* Currently, parallel directive is not supported. Notice that with a little effort by the programmer, any parallel region construct can be translated into a kernels region. Synchronization clause/APIs are not supprted as well. IPMACC generates a code to synchronize host and device after every kernels region.
* Only 1D array can be transfered in-out the region.
* Clause support: `seq` clause for the top-level 1-nested loop is not supported. This is weird case where there is only one loop in the region which is targeted for serial execution.
* There are some issues between NVCC and C's `restrict` keyword in CUDA 4.0.
* Limitations on the Reduction/Private clause of loop
    * For nested loops, reduction is only allowed over the most outer loop.
    * IPMACC assumes the reduction/private variable is not declared inside the loop.
    * If the variable is defined as both private() and reduction(), IPMACC assumes reduction which covers private too.
    * Reduction/Private on array/subarray is not supported
    * Default reduction type is two-level tree reduction [1]. Alternatively for CUDA, atomic reduction is implemented and it is supported only on recent hardwares (compute capability >= 1.3). Proper flag should be passed to underlying NVCC; add `-arch=sm_13` compile flag.
* To gurantee proper device allocation and release, it is necessary to use acc_init() early in the code to avoid potentially runtime errors. This is essential for the OpenCL target devices.
* IPMACC can parallel the iterations of loops with the following increment steps: +, -, ++, --, *, /

# Contributors:
* Ahmad Lashgar, University of Victoria
* Alireza Majidi, Texas A&M University
* Ebad Salehi, University of Victoria

# Publications:
**[1]** Ahmad Lashgar, Alireza Majidi, and Amirali Baniasadi, **"IPMACC: Open Source OpenACC to CUDA/OpenCL Translator"**, arXiv:1412.1127 [cs.PL], December 2, 2014.
**[2]** Ebad Salehi, Ahmad Lashgar, and Amirali Baniasadi, **"Compiler-Enhanced Memory Bandwidth Usage Reduction in OpenACC"**, In proceedings of the 30th ACM/SIGAPP Symposium On Applied Computing (SAC2015), Salamanca, Spain, April 13 - 17, 2015.
**[3]** Ahmad Lashgar, Alireza Majidi, and Amirali Baniasadi, **"IPMACC: Translating OpenACC API to OpenCL"**, To be appeared in The 3rd International Workshop on OpenCL (IWOCL), Stanford University, California, USA, May 11-13, 2015.

# References:
**[1]** Mark Hariss. Available: http://developer.download.nvidia.com/compute/cuda/1.1-Beta/x86_website/projects/reduction/doc/reduction.pdf

IPMACC translates and executes OpenACC for C applications over CUDA, OpenCL, and Intel ISPC. First, the framework translates OpenACC for C API to CUDA/OpenCL/ISPC source. Then, it compiles the CUDA/OpenCL/ISPC code with the system compiler allowing the execution of application over CUDA or OpenCL -capable devices or SIMD of the CPU (using ISPC).

IPMACC supports data, kernels, loop, enter, exit, and atomic directives. It also allows user-defiend data types and function calls within accelerator regions. We believe IPMACC is more of translator than a compiler, outputing the CUDA/OpenCL/ISPC code which is equivalent to the input OpenACC code. It allows further optimization by expert developer. We believe there can be performed many optimizations in translations, and this is what we are looking forward to. Also IPMACC can be used as a framework for extending OpenACC framework and evaluating new directive/clauses. Please refer to Limitation section of this document to overview supported directives and API calls.

# Getting Started:
* Refer to docs/ipmacc-openacc.pptx to learn basics of OpenACC.
* Refer to TODO document to see latest changes and the roadmap.
* Refer to INSTALL file for installation.
* Refer to docs/ipmacc-performance.pdf to see the performance comparison of OpenACC applications compiled by our implementation to native CUDA implementation.
* After the installation, the best way to start is to compile and run the samples in the test-case/ directory. Example:
```
    $ ipmacc test-case/vectorAdd.c -o vectorAdd
    $ ./vectorAdd
```
* There are microbenchmarks to evaluate the overhead of memory allocation, memory copies, and kernel launches under test-case/microbenchmarks/ directory. Also there are wide set of benchmarks under test-case/rodinia/


# Usage:
* IPMACC is a command-line tool reading single source and generating the destination source code (and also the object or binary). It has few limited compile switch. See the available switches with the following commands:

`$ ipmacc --help`

* In a case that there is a switch which IPMACC does not understands, IPMACC passes the switch to the system compiler. Hence, technically, IPMACC accepts all switches of the system compiler. The system compiler is `nvcc` in case of CUDA, `gcc` in case of OpenCL, and `gcc`/`ispc` in case of ISPC target. Examples:
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
* ISPC backend support is experimental right now. Only one loop can be executed in parallel (over SIMD). Planning to execute the second parallel loop over ISPC tasks. Also min, max, and sum reduction operations are only supported.

# Contributors:
* Ahmad Lashgar, University of Victoria
* Alireza Majidi, Texas A&M University
* Ebad Salehi, University of Victoria

# About IPMACC:
IPMACC is originally developed at Institute for Research in Fundamental Sciences (IPM), Tehran, Iran. We had an old outdated website on IPM page here http://hpc.ipm.ac.ir/ipmacc/. Follow our latest updates on https://github.com/lashgar/ipmacc

# Questions:
If you had any question or thinking of any issue, create a new issue thread here https://github.com/lashgar/ipmacc/issues or send an email to lashgar@uvic.ca

# Publications:
**[1]** Ahmad Lashgar, Alireza Majidi, and Amirali Baniasadi, **"IPMACC: Open Source OpenACC to CUDA/OpenCL Translator"**, arXiv:1412.1127 [cs.PL], December 2, 2014.

**[2]** Ahmad Lashgar, Alireza Majidi, and Amirali Baniasadi, **"IPMACC: Translating OpenACC API to OpenCL"**, To be appeared in The 3rd International Workshop on OpenCL (IWOCL), Stanford University, California, USA, May 11-13, 2015.

**[3]** Ahmad Lashgar and Amirali Baniasadi, **"Employing Software-Managed Caches in OpenACC: Opportunities and Benefits"**, To appear in ACM Transactions on Modeling and Performance Evaluation of Computing Systems (ToMPECS), Accepted on June 28, 2015.

# References:
**[1]** Mark Hariss. Available: http://developer.download.nvidia.com/compute/cuda/1.1-Beta/x86_website/projects/reduction/doc/reduction.pdf

**[2]** Matt Pharr and William R. Mark. **"ispc: A SPMD Compiler for High-Performance CPU Programming"**, In Proceedings Innovative Parallel Computing (InPar), San Jose, CA, May 2012.


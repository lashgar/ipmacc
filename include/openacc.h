// DISCLAIMER: THIS FILE IS DERIVED FROM openacc.h INCLUDED IN PGI COMPILER.


// for size_t
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <inttypes.h>
#include <unistd.h>
#include <math.h>
#include <string.h>

#define MSR_RAPL_POWER_UNIT		0x606

/* Package RAPL Domain */
#define MSR_PKG_RAPL_POWER_LIMIT	0x610
#define MSR_PKG_ENERGY_STATUS		0x611
#define MSR_PKG_PERF_STATUS		0x613
#define MSR_PKG_POWER_INFO		0x614

/* PP0 RAPL Domain */
#define MSR_PP0_POWER_LIMIT		0x638
#define MSR_PP0_ENERGY_STATUS		0x639
#define MSR_PP0_POLICY			0x63A
#define MSR_PP0_PERF_STATUS		0x63B

/* PP1 RAPL Domain, may reflect to uncore devices */
#define MSR_PP1_POWER_LIMIT		0x640
#define MSR_PP1_ENERGY_STATUS		0x641
#define MSR_PP1_POLICY			0x642

/* DRAM RAPL Domain */
#define MSR_DRAM_POWER_LIMIT		0x618
#define MSR_DRAM_ENERGY_STATUS		0x619
#define MSR_DRAM_PERF_STATUS		0x61B
#define MSR_DRAM_POWER_INFO		0x61C

/* RAPL UNIT BITMASK */
#define POWER_UNIT_OFFSET	0
#define POWER_UNIT_MASK		0x0F

#define ENERGY_UNIT_OFFSET	0x08
#define ENERGY_UNIT_MASK	0x1F00

#define TIME_UNIT_OFFSET	0x10
#define TIME_UNIT_MASK		0xF000

#define CPU_SANDYBRIDGE     42
#define CPU_SANDYBRIDGE_EP  45
#define CPU_IVYBRIDGE       58
#define CPU_IVYBRIDGE_EP    62





#ifndef __IPMACC_HEADER__
#define __IPMACC_HEADER__

typedef enum{
    acc_device_none = 0,
    acc_device_default = 1,
    acc_device_host = 2,
    acc_device_not_host = 3,
    acc_device_nvcuda = 4,
    acc_device_nvocl = 5,
    acc_device_intelocl = 6
} acc_device_t;

#ifndef __PGI_ULLONG
#ifdef TARGET_WIN_X8664
#define __PGI_ULLONG unsigned long long
#else
#define __PGI_ULLONG unsigned long
#endif
#endif


#ifdef __cplusplus
extern "C" int acc_get_num_devices( acc_device_t devtype );
extern "C" void acc_set_device_type( acc_device_t devtype );
extern "C" acc_device_t acc_get_device_type(void);
extern "C" void acc_set_device_num( int devnum, acc_device_t devtype );
extern "C" int acc_get_device_num( acc_device_t devtype );
extern "C" void acc_init( acc_device_t devtype );
extern "C" void acc_shutdown( acc_device_t devtype );
extern "C" void* acc_malloc(size_t size);
extern "C" void acc_free(void*);
extern "C" void* acc_deviceptr( void* hostptr );
extern "C" void* acc_create( void* hostptr, size_t bytes );
extern "C" void* acc_present_or_create ( void*, size_t );
extern "C" void* acc_pcreate ( void*, size_t );
extern "C" void* acc_copyin( void* hostptr, size_t bytes );
extern "C" void* acc_present_or_copyin ( void*, size_t );
extern "C" void* acc_pcopyin ( void*, size_t );
extern "C" void acc_copyout ( void*, size_t );
extern "C" void acc_delete ( void*, size_t );
extern "C" void* acc_hostptr ( void* );
extern "C" int acc_is_present ( void*, size_t );
#else
extern int acc_get_num_devices( acc_device_t devtype );
extern void acc_set_device_type( acc_device_t devtype );
extern acc_device_t acc_get_device_type(void);
extern void acc_set_device_num( int devnum, acc_device_t devtype );
extern int acc_get_device_num( acc_device_t devtype );
extern void acc_init( acc_device_t devtype );
extern void acc_shutdown( acc_device_t devtype );
extern void* acc_malloc(size_t size);
extern void acc_free(void*);
extern void* acc_deviceptr( void* hostptr );
extern void* acc_create( void* hostptr, size_t bytes );
extern void* acc_present_or_create ( void*, size_t );
extern void* acc_pcreate ( void*, size_t );
extern void* acc_copyin( void* hostptr, size_t bytes );
extern void* acc_present_or_copyin ( void*, size_t );
extern void* acc_pcopyin ( void*, size_t );
extern void acc_copyout ( void*, size_t );
extern void acc_delete ( void*, size_t );
extern void* acc_hostptr ( void* );
extern int acc_is_present ( void*, size_t );
#endif

/* IPM Additions */
#ifdef __cplusplus
extern "C" void acc_list_devices_spec( acc_device_t devtype );
extern "C" void acc_copyout_and_keep ( void*hostptr, size_t bytes);
extern "C" void* acc_present( void *hostptr);
extern "C" void ipmacc_prompt(char *s);
extern "C" int open_msr(int core) ;
extern "C" long long read_msr(int fd, int which) ;
extern "C" int detect_cpu(void) ;
extern "C" int getEnergy( double *packageEnergy, double *coreEnergy, int core);
extern "C" void acc_get_mem_info(size_t *free, size_t *total);
#else
extern void acc_list_devices_spec( acc_device_t devtype );
extern void acc_copyout_and_keep ( void*hostptr, size_t bytes);
extern void* acc_present( void *hostptr);
extern void ipmacc_prompt(char *s);
extern int open_msr(int core) ;
extern long long read_msr(int fd, int which) ;
extern int detect_cpu(void) ;
extern int getEnergy( double *packageEnergy, double *coreEnergy, int core);
extern void acc_get_mem_info(size_t *free, size_t *total);
#endif

/* PGI Additions */
extern void acc_updatein( void* hostptr, __PGI_ULLONG bytes );
extern void acc_update_device( void* hostptr, __PGI_ULLONG bytes );
extern void acc_updateout( void* hostptr, __PGI_ULLONG bytes );
extern void acc_update_host( void* hostptr, __PGI_ULLONG bytes );
#define pgi_async_sync	0
#define pgi_async_noval	1
#define acc_async_sync	0
#define acc_async_noval	1

// unimplemented functions
extern int acc_async_test( acc_device_t devtype );
extern int acc_async_test_all();
extern void acc_async_wait( acc_device_t devtype );
extern void acc_async_wait_all();
extern int acc_on_device( acc_device_t devtype );


/* IPM ACC Include files */

/////////////////////
// INTERNAL IPMACC //
// //////////////////
/* IPM ACC Include files */
/* TRAINING */
#ifdef __cplusplus
extern "C" void* acc_training_kernel_add(const char *kernelSource, char *compileFlags, char *kernelName, int kernelId, int nargs);
extern "C" void* acc_training_decide_command_queue(int kernelId);
extern "C" void* acc_training_kernel_start(int kernelId);
extern "C" void* acc_training_kernel_end();
#else
extern void* acc_training_kernel_add(const char *kernelSource, char *compileFlags, char *kernelName, int kernelId, int nargs);
extern void* acc_training_decide_command_queue(int kernelId);
extern void* acc_training_kernel_start(int kernelId);
extern void* acc_training_kernel_end();
#endif


/*
#ifdef __cplusplus
extern "C" void __ipmacc_opencl_prekernel(const char *kernelSource);
extern "C" void __ipmacc_opencl_setarg(void** ptr, size_t bytes, cl_uint index);
#else
extern void __ipmacc_opencl_prekernel(const char *kernelSource);
extern void __ipmacc_opencl_setarg(void** ptr, size_t bytes, cl_uint index);
#endif
*/


#endif

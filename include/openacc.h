
// for size_t
#include <stdio.h>


#ifndef __IPMACC_HEADER__
#define __IPMACC_HEADER__

typedef enum{
    acc_device_none = 0,
    acc_device_default = 1,
    acc_device_host = 2,
    acc_device_not_host = 3,
    acc_device_nvcuda = 4,
    acc_device_nvocl = 5
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
#else
extern void acc_list_devices_spec( acc_device_t devtype );
extern void acc_copyout_and_keep ( void*hostptr, size_t bytes);
extern void* acc_present( void *hostptr);
extern void ipmacc_prompt(char *s);
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

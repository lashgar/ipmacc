/* 
 *
 *      Copyright 2008-2011, STMicroelectronics, Incorporated.
 *      All rights reserved.
 *
 *        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
 * This software is supplied under the terms of a license agreement
 * or nondisclosure agreement with STMicroelectronics and may not be
 * copied or disclosed except in accordance with the terms of that
 * agreement.
 */

typedef enum{
	acc_device_none = 0,
	acc_device_default = 1,
	acc_device_host = 2,
	acc_device_not_host = 3,
	acc_device_nvidia = 4
    }acc_device_t;

#ifdef TARGET_WIN_X8664
#define ULLONG unsigned long long
#else
#define ULLONG unsigned long
#endif


extern int acc_get_num_devices( acc_device_t devtype );
extern void acc_set_device( acc_device_t devtype );
extern acc_device_t acc_get_device(void);
extern void acc_set_device_num( int devnum, acc_device_t devtype );
extern int acc_get_device_num( acc_device_t devtype );
extern void acc_init( acc_device_t devtype );
extern void acc_shutdown( acc_device_t devtype );
extern void acc_sync( acc_device_t devtype );
extern ULLONG acc_get_memory();
extern ULLONG acc_get_free_memory();
extern void* acc_malloc(ULLONG);
extern void acc_free(void*);
extern unsigned int acc_regions(void);
extern unsigned int acc_kernels(void);
extern unsigned int acc_allocs(void);
extern unsigned int acc_frees(void);
extern unsigned int acc_copyins(void);
extern unsigned int acc_copyouts(void);
extern ULLONG acc_bytesalloc(void);
extern ULLONG acc_bytesin(void);
extern ULLONG acc_bytesout(void);
extern int acc_active(acc_device_t);
extern ULLONG acc_total_time(acc_device_t);
extern ULLONG acc_exec_time(acc_device_t);
extern void acc_enable_time(acc_device_t);
extern void acc_disable_time(acc_device_t);
extern int acc_async_test( int q );
extern int acc_async_test_all();
extern void acc_async_wait( int q );
extern void acc_async_wait_all();
extern int acc_on_device(acc_device_t);
extern void* acc_deviceptr(void*);

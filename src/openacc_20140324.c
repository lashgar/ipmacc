
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "msr.h"
///////////////////////////
// INTERFACING FUNCTIONS //
///////////////////////////
void ipmacc_prompt(char *s){
    if (getenv("IPMACC_VERBOSE"))
        printf("%s",s);
}

/////////////////////////////////////////
// INTERNAL DEVICE-HOST MEMORY MAPPING //
/////////////////////////////////////////
typedef struct openacc_ipmacc_varmapper_s{
    void *src, *des;
    size_t size;
    struct openacc_ipmacc_varmapper_s *next;
}openacc_ipmacc_varmapper_t;

openacc_ipmacc_varmapper_t *openacc_ipmacc_varmapper_head= NULL;
void openacc_ipmacc_insert(void *src, void *des, size_t size)
{
    openacc_ipmacc_varmapper_t * newElement = (openacc_ipmacc_varmapper_t*)malloc(sizeof(openacc_ipmacc_varmapper_t));
    newElement->src = src ;
    newElement->des = des ;
    newElement->size = size ;
    newElement->next = NULL ;
    if(openacc_ipmacc_varmapper_head == NULL)
        openacc_ipmacc_varmapper_head = newElement ;
    else
    {
        newElement->next = openacc_ipmacc_varmapper_head ;
        openacc_ipmacc_varmapper_head = newElement;
    }
}
void* openacc_ipmacc_get(void *src)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            return temp->des ;
        }
        temp = temp->next;
    }
    return NULL ;
}
void* openacc_ipmacc_reverse_get(void *des)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->des == des )
        {
            return temp->src ;
        }
        temp = temp->next;
    }
    return NULL ;
}


////////////////////////
// EXTERNAL INTERFACE //
////////////////////////

typedef enum{
    acc_device_none = 0,
    acc_device_default = 1,
    acc_device_host = 2,
    acc_device_not_host = 3,
    acc_device_nvcuda = 4,
    acc_device_nvocl = 5
}acc_device_t;


//int __ipmacc_devicetype=acc_device_none;
int __ipmacc_devicenum=0;

#ifdef __NVCUDA__
#define __IPMACC_DESTINATION__ 1
#include <cuda.h>
#include <cuda_runtime.h>
int __ipmacc_devicetype=acc_device_nvcuda;
#endif

#ifdef __NVOPENCL__
#ifndef __IPMACC_DESTINATION__
#define __IPMACC_DESTINATION__ 2
int __ipmacc_devicetype=acc_device_nvocl;
#endif
#include <CL/cl.h>
cl_int __ipmacc_clerr = CL_SUCCESS;
cl_context __ipmacc_clctx = NULL;
size_t __ipmacc_parmsz;
cl_device_id* __ipmacc_cldevs = NULL;
cl_command_queue __ipmacc_command_queue = NULL;
cl_kernel __ipmacc_clkern;
#endif

///////////////////////
//Energy Variables////
//////////////////////
double package0_before, package0_after;
double package1_before, package1_after;
double core0_before, core0_after;
double core8_before, core8_after;


#define PACKAGE0 0
#define PACKAGE1 1

#define PACKAGE0_CORE 0
#define PACKAGE1_CORE 8



#ifndef __IPMACC_DESTINATION__
// perform a fallback to CUDA
#define __IPMACC_DESTINATION__ 1
#include <cuda.h>
int __ipmacc_devicetype=acc_device_nvcuda;
#endif

#include <stdio.h>

int acc_get_num_devices( acc_device_t devtype ){
    int count=-1;
    if(devtype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        cudaGetDeviceCount(&count);
#endif 
        return count;
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_set_device_type( acc_device_t devtype ){
    int count=-1;
    if(devtype==acc_device_nvcuda){
        //CUDA on NV
        __ipmacc_devicetype=acc_device_nvcuda;
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
acc_device_t acc_get_device_type(void){
    return __ipmacc_devicetype;
}
void acc_set_device_num( int devnum, acc_device_t devtype ){
    if(devtype==acc_device_nvcuda){
        //CUDA on NV
        if(acc_get_num_devices(devtype)>devnum){
#ifdef __NVCUDA__
            cudaSetDevice(devnum);
#endif 
            __ipmacc_devicenum=devnum;
        }else{
            fprintf(stderr,"The specified device does not exists!\naborting\n");
            exit(-1);
        }
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
int acc_get_device_num( acc_device_t devtype ){
    return __ipmacc_devicenum;
}
// int acc_async_test( acc_device_t devtype );
// int acc_async_test_all();
// void acc_async_wait( acc_device_t devtype );
// void acc_async_wait_all();
void* acc_partition_device(cl_device_id *device_to_partition, acc_device_t devtype  ){
    if(devtype==acc_device_nvcuda){
#ifdef __NVCUDA__
        fprintf(stderr,"Device partitioning is not supported on CUDA\n");
        exit(-1);
#endif 
    }else if(devtype==acc_device_nvocl){
#ifdef __NVOPENCL__
        unsigned int ncore_per_partition=0;
        sscanf(getenv("IPMACC_DEVICE_PART"),"%u",&ncore_per_partition);
        assert(ncore_per_partition>0);
        int i;
        const cl_device_partition_property prop[]={CL_DEVICE_PARTITION_EQUALLY,ncore_per_partition,0};
        cl_uint subdeviceCount_g=32; // guess number of sub-devices
        cl_uint subdeviceCount_r=-1;
        cl_device_id *subdevices=(cl_device_id*)malloc(sizeof(cl_device_id)*subdeviceCount_g);
        cl_int error=clCreateSubDevices( (*device_to_partition),
                prop,
                subdeviceCount_g,
                subdevices,
                &subdeviceCount_r);
        if(subdevices==NULL || subdeviceCount_r==-1){
            fprintf(stderr,"\t failed to parition the device: error %d\n",error);
            exit(-1);
        }else{
            printf("\t device is partitioned into %d subdevices\n",subdeviceCount_r);
            printf("\t root device id: %u\n\t subdevices: ",device_to_partition);
            for(i=0; i<subdeviceCount_r; i++)
                printf("%u, ",subdevices[i]);
            printf("\n");
        }
        return (void*)subdevices;
#endif 
    }
}
void acc_init( acc_device_t devtype ){
#ifdef RALP
	getEnergy( &package0_before, &core0_before, PACKAGE0_CORE);
	getEnergy( &package1_before, &core8_before, PACKAGE1_CORE);
//	printf("current energy for package#%d: %.6f\n", PACKAGE0, package0_before);
//	printf("current energy for package#%d: %.6f\n", PACKAGE1, package1_before);
//	printf("current energy for core#%d: %.6f\n", PACKAGE0_CORE, core0_before);
//	printf("current energy for core#%d: %.6f\n", PACKAGE1_CORE, core8_before);
#endif

	if(devtype==acc_device_nvcuda){
        //CUDA on NV
        if(acc_get_num_devices(devtype)>0){
#ifdef __NVCUDA__
            cudaSetDevice(0);
#endif 
        }else{
            fprintf(stderr,"The specified device type does not exists!\naborting\n");
            exit(-1);
        }
        if(getenv("IPMACCLIB_VERBOSE")) printf("CUDA: device init.\n");
        __ipmacc_devicetype=acc_device_nvcuda;
    }else if(devtype==acc_device_nvocl){
#ifdef __NVOPENCL__
        cl_platform_id platform_id = NULL;
        cl_device_id device_id = NULL;   
        cl_uint ret_num_devices;
        cl_uint ret_num_platforms;
        __ipmacc_clerr = clGetPlatformIDs(1, &platform_id, &ret_num_platforms);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("Runtime error! unable to find any OpenCL-enabled platform\n");
            printf("Check the installation of system OpenCL driver\n");
            exit(-1);
        }
        __ipmacc_clerr = clGetDeviceIDs( platform_id, CL_DEVICE_TYPE_DEFAULT, 1, &device_id, &ret_num_devices);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("Runtime error! unable to retrieve the device id of CL_DEVICE_TYPE_DEFAULT\n");
            exit(-1);
        }
        // select device
        if(getenv("IPMACC_DEVICE_PART")==NULL){
            __ipmacc_cldevs=(cl_device_id*)malloc(sizeof(cl_device_id)*1);
    	    __ipmacc_cldevs[0]=device_id;
        }else{
            // create subdevices
            cl_device_id *subdevices=(cl_device_id*)acc_partition_device(&device_id,devtype);
            assert(subdevices!=NULL);
            __ipmacc_cldevs=subdevices;
        }
        // Create an OpenCL context
        __ipmacc_clctx = clCreateContext( NULL, 1, &__ipmacc_cldevs[0], NULL, NULL, &__ipmacc_clerr);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("Runtime error! Cannot open context on the device %d of CL_DEVICE_TYPE_DEFAULT\n",__ipmacc_cldevs[0]);
            exit(-1);
        }

        // Create a command queue
        __ipmacc_command_queue = clCreateCommandQueue(__ipmacc_clctx, __ipmacc_cldevs[0], 0, &__ipmacc_clerr);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("Runtime error! Cannot creat command queue on the device %d of CL_DEVICE_TYPE_DEFAULT\n",__ipmacc_cldevs[0]);
            exit(-1);
        }
        if(getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: device init.\n");
        __ipmacc_devicetype=acc_device_nvocl;
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_shutdown( acc_device_t devtype ){

#ifdef RALP
	getEnergy( &package0_after, &core0_after, PACKAGE0_CORE);
	getEnergy( &package1_after, &core8_after, PACKAGE1_CORE);
	printf("consumed energy for package#%d: %.6f\n", PACKAGE0, package0_after - package0_before);
	printf("consumed energy for package#%d: %.6f\n", PACKAGE1, package1_after - package1_before);
	printf("consumed energy for core#%d: %.6f\n", PACKAGE0_CORE, core0_after - core0_before);
	printf("consumed energy for core#%d: %.6f\n", PACKAGE1_CORE, core8_after - core8_before);
#endif



    if(devtype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        cudaDeviceReset();
#endif
    }else if(acc_get_num_devices(devtype)>0){
#ifdef __NVOPENCL__
	
#endif 
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}


// int acc_on_device( acc_device_t devtype );
void* acc_malloc(size_t size){
    if(__ipmacc_devicetype==acc_device_nvcuda){
        //CUDA on NV
        void *ptr=NULL;
#ifdef __NVCUDA__
        cudaMalloc((void**)&ptr,size);
#endif 
        return ptr;
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_free(void *ptr){
    if(__ipmacc_devicetype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        cudaFree(ptr);
#endif 
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}

/* IPM Additions */
void acc_list_devices_spec( acc_device_t devtype ){
    if(devtype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
#endif 
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }else if(devtype==acc_device_nvocl){
#ifdef __NVOPENCL__
        // this code is imported from [1] with minor modifications.
        // [1] http://dhruba.name/2012/08/14/opencl-cookbook-listing-all-devices-and-their-critical-attributes/
        int i, j;
        char* value;
        size_t valueSize;
        cl_uint platformCount;
        cl_platform_id* platforms;
        cl_uint deviceCount;
        cl_device_id* devices;
        cl_uint maxComputeUnits, maxWorkItemDim;
        size_t maxWorkGroups;
        size_t maxWorkItemSize[3];

        char * platform_name ;
        int platform_name_size ;
	// get all platforms
        clGetPlatformIDs(0, NULL, &platformCount);
        platforms = (cl_platform_id*) malloc(sizeof(cl_platform_id) * platformCount);
        clGetPlatformIDs(platformCount, platforms, NULL);

        for (i = 0; i < platformCount; i++) {
	    clGetPlatformInfo(platforms[i],CL_PLATFORM_NAME, 0, NULL, &platform_name_size);
            platform_name = (char *)malloc(sizeof(char)*platform_name_size);
            clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, platform_name_size, platform_name, NULL);
            printf("platform name: %s\n", platform_name);

            // get all devices
            clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_ALL, 0, NULL, &deviceCount);
            devices = (cl_device_id*) malloc(sizeof(cl_device_id) * deviceCount);
            clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_ALL, deviceCount, devices, NULL);

            // for each device print critical attributes
            for (j = 0; j < deviceCount; j++) {

                // print device name
                clGetDeviceInfo(devices[j], CL_DEVICE_NAME, 0, NULL, &valueSize);
                value = (char*) malloc(valueSize);
                clGetDeviceInfo(devices[j], CL_DEVICE_NAME, valueSize, value, NULL);
                printf("%d. Device: %s\n", j+1, value);
                free(value);

                // print hardware device version
                clGetDeviceInfo(devices[j], CL_DEVICE_VERSION, 0, NULL, &valueSize);
                value = (char*) malloc(valueSize);
                clGetDeviceInfo(devices[j], CL_DEVICE_VERSION, valueSize, value, NULL);
                printf(" %d.%d Hardware version: %s\n", j+1, 1, value);
                free(value);

                // print software driver version
                clGetDeviceInfo(devices[j], CL_DRIVER_VERSION, 0, NULL, &valueSize);
                value = (char*) malloc(valueSize);
                clGetDeviceInfo(devices[j], CL_DRIVER_VERSION, valueSize, value, NULL);
                printf(" %d.%d Software version: %s\n", j+1, 2, value);
                free(value);

                // print c version supported by compiler for device
                clGetDeviceInfo(devices[j], CL_DEVICE_OPENCL_C_VERSION, 0, NULL, &valueSize);
                value = (char*) malloc(valueSize);
                clGetDeviceInfo(devices[j], CL_DEVICE_OPENCL_C_VERSION, valueSize, value, NULL);
                printf(" %d.%d OpenCL C version: %s\n", j+1, 3, value);
                free(value);

                // print parallel compute units
                clGetDeviceInfo(devices[j], CL_DEVICE_MAX_COMPUTE_UNITS,
                        sizeof(maxComputeUnits), &maxComputeUnits, NULL);
                printf(" %d.%d Parallel compute units: %d\n", j+1, 4, maxComputeUnits);

                // print maximum CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS
                clGetDeviceInfo(devices[j], CL_DEVICE_MAX_WORK_ITEM_DIMENSIONS,
                        sizeof(maxWorkItemDim), &maxWorkItemDim, NULL);
                printf(" %d.%d Maximum work-item dimenstions: %d\n", j+1, 5, maxWorkItemDim);

                // print maximum CL_DEVICE_MAX_WORK_GROUP_SIZE
                clGetDeviceInfo(devices[j], CL_DEVICE_MAX_WORK_GROUP_SIZE,
                        sizeof(maxWorkGroups), &maxWorkGroups, NULL);
                printf(" %d.%d Maximum work-group size: %d\n", j+1, 6, maxWorkGroups);

                // print maximum CL_DEVICE_MAX_WORK_ITEM_SIZE
                clGetDeviceInfo(devices[j], CL_DEVICE_MAX_WORK_ITEM_SIZES,
                        sizeof(maxWorkItemSize), &maxWorkItemSize, NULL);
                printf(" %d.%d Maximum work-item size: %dx%dx%d\n", j+1, 7, maxWorkItemSize[0], maxWorkItemSize[1], maxWorkItemSize[2]);
            }

            free(devices);

        }

        free(platforms);
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }

}

//#define DEBUG_LIB 0
void* acc_deviceptr( void* hostptr )
{
    return openacc_ipmacc_get(hostptr);
}
void* acc_create( void* hostptr, size_t bytes )
{
    void *devptr=NULL;
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        cudaError_t err=cudaMalloc((void**)&devptr,bytes);
        if(err!=cudaSuccess){
            printf("failed to allocate memory %16llu bytes on CUDA device: %d\n", bytes, __ipmacc_clerr);
        }else if(getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [allocated] on device (ptr: %p)\n",bytes,devptr);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl){
#ifdef __NVOPENCL__
        devptr=(void*)clCreateBuffer(__ipmacc_clctx, CL_MEM_READ_WRITE, bytes, NULL, &__ipmacc_clerr);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("failed to allocate memory %16llu bytes on OpenCL device: %d\n", bytes, __ipmacc_clerr);
        }else{
            if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [allocated] on device (ptr: %p)\n",bytes,devptr);
        }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
    assert(devptr!=NULL);
    openacc_ipmacc_insert(hostptr, devptr, bytes);
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: create devpointer %p\n",devptr);
#endif
    return devptr;
}
void* acc_present_or_create ( void* hostptr, size_t bytes)
{
    void *devptr=acc_deviceptr(hostptr);
    if(devptr){
        return devptr ;
    }else{
        devptr = acc_create(hostptr, bytes);
    }
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: create devpointer %p\n",devptr);
#endif
    return devptr;
}
void* acc_pcreate ( void* hostptr, size_t bytes)
{
    return acc_present_or_create(hostptr, bytes);
}
void* acc_present( void* hostptr)
{
    void* devptr=acc_deviceptr(hostptr);
    if(devptr==NULL){
        printf("Data is not found on the device!\n");
        exit(-1);
    }else{
        return devptr;
    }
}

void acc_copyout_and_keep ( void * hostptr, size_t bytes)
{
    // copy the data from device back to host
    void* devptr=acc_deviceptr(hostptr);
    if(devptr==NULL){
        printf("Data is not found on the device!\n");
        exit(-1);
    }
    //copyin
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyout devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes,devptr);
        cudaMemcpy(hostptr, devptr, bytes, cudaMemcpyDeviceToHost);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes);
        clEnqueueReadBuffer(__ipmacc_command_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_delete ( void*hostptr, size_t bytes)
{
    // free memory
}   
void acc_copyout ( void* hostptr, size_t bytes )
{
    // copyout_keep
    acc_copyout_and_keep ( hostptr, bytes);

    // delete
    acc_delete(hostptr, bytes);
}
void* acc_hostptr ( void* devptr)
{
    return openacc_ipmacc_reverse_get( devptr );
}
int acc_is_present ( void* hostptr, size_t bytes)
{
    return acc_deviceptr(hostptr)!=NULL;

}
void* acc_present_or_copyin( void* hostptr, size_t bytes )
{
    void* devptr=acc_deviceptr(hostptr);
    if(devptr==NULL){
        //create
        devptr = acc_create( hostptr, bytes);
#ifdef DEBUG_LIB 
        printf("ipmacc: pcopyin create devpointer %p\n",devptr);
#endif
    }
    //copyin
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyin devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyin]    to device (ptr: %p)\n",bytes,devptr);
        cudaMemcpy(devptr, hostptr, bytes, cudaMemcpyHostToDevice); 
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyin]    from device (ptr: %p)\n",bytes,devptr);
        clEnqueueWriteBuffer(__ipmacc_command_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
    return devptr ;
} 

void* acc_copyin( void* hostptr, size_t bytes )
{
    void * devptr = acc_create( hostptr, bytes );
    return  acc_present_or_copyin( hostptr, bytes);
}
void* acc_pcopyin ( void* hostptr , size_t bytes )
{
    return acc_present_or_copyin( hostptr, bytes);
}



/////////////////////
// INTERNAL IPMACC //
// //////////////////
/*
void __ipmacc_opencl_setarg(void** ptr, size_t bytes, cl_uint index)
{
    assert(ptr);
    __ipmacc_clerr=clSetKernelArg(__ipmacc_clkern, index, bytes, ptr);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clSetKernelArg! id: %d\n",__ipmacc_clerr);
        exit(-1);
    }
}

void __ipmacc_opencl_prekernel(const char *kernelSource)
{
    cl_program __ipmacc_clpgm;
    __ipmacc_clpgm=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource, NULL, &__ipmacc_clerr);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
        exit(-1);
    }
    char __ipmacc_clcompileflags[128];
    sprintf(__ipmacc_clcompileflags, " ");
    clBuildProgram(__ipmacc_clpgm, 0, NULL, __ipmacc_clcompileflags, NULL, NULL);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);
        exit(-1);
    }
    __ipmacc_clkern = clCreateKernel(__ipmacc_clpgm, "__generated_kernel_region_0", &__ipmacc_clerr);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
        exit(-1);
    }
}
*
*/



//////////////////////////////////////////
// power calculating usong msr_ralp_read//
// //////////////////////////////////////


int open_msr(int core) {

	char msr_filename[BUFSIZ];
	int fd;

	sprintf(msr_filename, "/dev/cpu/%d/msr", core);
	fd = open(msr_filename, O_RDONLY);
	if ( fd < 0 ) {
		if ( errno == ENXIO ) {
			fprintf(stderr, "rdmsr: No CPU %d\n", core);
			exit(2);
		} else if ( errno == EIO ) {
			fprintf(stderr, "rdmsr: CPU %d doesn't support MSRs\n", core);
			exit(3);
		} else {
			perror("rdmsr:open");
			fprintf(stderr,"Trying to open %s\n",msr_filename);
			exit(127);
		}
	}

	return fd;
}

long long read_msr(int fd, int which) {

	uint64_t data;

	if ( pread(fd, &data, sizeof data, which) != sizeof data ) {
		perror("rdmsr:pread");
		exit(127);
	}

	return (long long)data;
}

int detect_cpu(void) {

	FILE *fff;

	int family,model=-1;
	char buffer[BUFSIZ],*result;
	char vendor[BUFSIZ];

	fff=fopen("/proc/cpuinfo","r");
	if (fff==NULL) return -1;

	while(1) {
		result=fgets(buffer,BUFSIZ,fff);
		if (result==NULL) break;

		if (!strncmp(result,"vendor_id",8)) {
			sscanf(result,"%*s%*s%s",vendor);

			if (strncmp(vendor,"GenuineIntel",12)) {
				printf("%s not an Intel chip\n",vendor);
				return -1;
			}
		}

		if (!strncmp(result,"cpu family",10)) {
			sscanf(result,"%*s%*s%*s%d",&family);
			if (family!=6) {
				printf("Wrong CPU family %d\n",family);
				return -1;
			}
		}

		if (!strncmp(result,"model",5)) {
			sscanf(result,"%*s%*s%d",&model);
		}

	}

	fclose(fff);
	switch(model) {
		case CPU_SANDYBRIDGE:
//			printf("Found Sandybridge CPU\n");
			break;
		case CPU_SANDYBRIDGE_EP:
//			printf("Found Sandybridge-EP CPU\n");
			break;
		case CPU_IVYBRIDGE:
//			printf("Found Ivybridge CPU\n");
			break;
		case CPU_IVYBRIDGE_EP:
//			printf("Found Ivybridge-EP CPU\n");
			break;
		default:	//printf("Unsupported model %d\n",model);
				model=-1;
				break;
	}

	return model;
}

int getEnergy( double *packageEnergy, double *coreEnergy, int core){
	int fd;
	long long result;
	double power_units,energy_units,time_units;
	double package_before,package_after;
	double pp0_before,pp0_after;
	double pp1_before=0.0,pp1_after;
	double dram_before=0.0,dram_after;
	double thermal_spec_power,minimum_power,maximum_power,time_window;
	int cpu_model;

	printf("\n");

	cpu_model=detect_cpu();
	if (cpu_model<0) {
		printf("Unsupported CPU type\n");
		return -1;
	}

	fd=open_msr(core);

	/* Calculate the units used */
	result=read_msr(fd,MSR_RAPL_POWER_UNIT);  
	power_units=pow(0.5,(double)(result&0xf));
	energy_units=pow(0.5,(double)((result>>8)&0x1f));
	time_units=pow(0.5,(double)((result>>16)&0xf));

	result=read_msr(fd,MSR_PKG_POWER_INFO);  
	thermal_spec_power=power_units*(double)(result&0x7fff);
	minimum_power=power_units*(double)((result>>16)&0x7fff);
	maximum_power=power_units*(double)((result>>32)&0x7fff);
	time_window=time_units*(double)((result>>48)&0x7fff);

	result=read_msr(fd,MSR_RAPL_POWER_UNIT);


	result=read_msr(fd,MSR_PKG_ENERGY_STATUS);  
	*packageEnergy=(double)result*energy_units;
	//printf("Package energy before: %.6fJ\n",package_before);

	result=read_msr(fd,MSR_PP0_ENERGY_STATUS);  
	*coreEnergy=(double)result*energy_units;
	//printf("PowerPlane0 (core) for core %d energy before: %.6fJ\n",core,pp0_before);

	/* not available on SandyBridge-EP */
	if ((cpu_model==CPU_SANDYBRIDGE) || (cpu_model==CPU_IVYBRIDGE)) {
		result=read_msr(fd,MSR_PP1_ENERGY_STATUS);  
		pp1_before=(double)result*energy_units;
		// printf("PowerPlane1 (on-core GPU if avail) before: %.6fJ\n",pp1_before);
	}
	else {
		result=read_msr(fd,MSR_DRAM_ENERGY_STATUS);
		dram_before=(double)result*energy_units;
		//printf("DRAM energy before: %.6fJ\n",dram_before);
	}

	return 0;
}




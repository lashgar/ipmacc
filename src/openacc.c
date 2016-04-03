
#include "common.h"

/////////////////////////////////////////
// INTERNAL DEVICE-HOST MEMORY MAPPING //
/////////////////////////////////////////
typedef struct openacc_ipmacc_varmapper_s{
    void *src; // host pointer
    void *des; // accelerator pointer
    size_t size;
    void *src_comp;
    void *des_coef;
    int compRatio;
    char type;
    float fcoef1, fcoef2;
    double dcoef1, dcoef2;
    struct openacc_ipmacc_varmapper_s *next;
}openacc_ipmacc_varmapper_t;

openacc_ipmacc_varmapper_t *openacc_ipmacc_varmapper_head= NULL;
void openacc_ipmacc_insert(void *src, void *des, size_t size)
{
    openacc_ipmacc_varmapper_t * newElement = (openacc_ipmacc_varmapper_t*)malloc(sizeof(openacc_ipmacc_varmapper_t));
    newElement->src = src ;
    newElement->des = des ;
    newElement->size = size ;
    newElement->src_comp = NULL;
    newElement->des_coef = NULL;
    newElement->next = NULL ;
    if(openacc_ipmacc_varmapper_head == NULL)
        openacc_ipmacc_varmapper_head = newElement ;
    else
    {
        newElement->next = openacc_ipmacc_varmapper_head ;
        openacc_ipmacc_varmapper_head = newElement;
    }
}
int openacc_ipmacc_set_comp(void *src, void *compPtr)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            temp->src_comp=compPtr;
            return 1;
        }
        temp = temp->next;
    }
    return 0 ;
}
void * openacc_ipmacc_get_comp(void *src)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            return temp->src_comp;
        }
        temp = temp->next;
    }
    return NULL ;
}
int openacc_ipmacc_set_compRatio(void *src, int compRatio)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            temp->compRatio=compRatio;
            return 1;
        }
        temp = temp->next;
    }
    return 0 ;
}
int openacc_ipmacc_set_coef(void *src, void *coef)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            temp->des_coef=coef;
            return 1;
        }
        temp = temp->next;
    }
    return 0 ;
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
openacc_ipmacc_varmapper_t * openacc_ipmacc_get_object(void *src)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            return temp;
        }
        temp = temp->next;
    }
    return NULL ;
}
void* openacc_ipmacc_unmap_memory(void *hostptr)
{
    // remove the host-accelerator entry in the list
    // and return the accelerator pointer
    // returns NULL if the hostptr is not in the list
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    openacc_ipmacc_varmapper_t * prev = temp;
    while(temp != NULL)
    {
        if(temp->src == hostptr)
        {
            // pointer found!
            // remove it:
            void *deviceptr = temp->des;
            if(prev==temp){
                // removing the head
                openacc_ipmacc_varmapper_head=temp->next;
            }else{
                prev->next=temp->next;
            }
            temp->next=NULL;
            free(temp);
            return deviceptr;
        }
        prev = temp;
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
    acc_device_nvocl = 5,
    acc_device_intelocl = 6
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

#ifdef cl_device_partition_property
#define __NVOPENCL12__
#endif

cl_int __ipmacc_clerr = CL_SUCCESS;
cl_context __ipmacc_clctx = NULL;
size_t __ipmacc_parmsz;
cl_device_id* __ipmacc_cldevs = NULL;
unsigned int __ipmacc_clnpartition = 0;
cl_command_queue __ipmacc_command_queue = NULL, __ipmacc_temp_cmdqueue=NULL;
cl_command_queue *__ipmacc_clpartitions_command_queues = NULL;
int __ipmacc_training_outstanding_kernel_id=-1;
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

/////////////////////
// timing variable///
////////////////////
struct timeval t1,t2;

#ifndef __IPMACC_DESTINATION__
// perform a fallback to CUDA
#define __IPMACC_DESTINATION__ 1
#include <cuda.h>
int __ipmacc_devicetype=acc_device_nvcuda;
#endif

#include <stdio.h>

void* acc_isComp(void *src){
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            return temp->src_comp ;
        }
        temp = temp->next;
    }
    return NULL ;
}
void* acc_get_coef(void *src)
{
    openacc_ipmacc_varmapper_t * temp = openacc_ipmacc_varmapper_head;
    while(temp != NULL)
    {
        if(temp->src == src )
        {
            void *dev_coef;
            cudaGetSymbolAddress(&dev_coef,temp->des_coef);
            return dev_coef;
        }
        temp = temp->next;
    }
    return NULL ;
}
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
        __ipmacc_devicetype=devtype;
    }else if(devtype==acc_device_nvocl || devtype==acc_device_intelocl){
        //OpenCL platform
        __ipmacc_devicetype=devtype;
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
    if(devtype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        return __ipmacc_devicenum;
#endif 
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
// int acc_async_test( acc_device_t devtype );
// int acc_async_test_all();
// void acc_async_wait( acc_device_t devtype );
// void acc_async_wait_all();
void* acc_partition_device(void *device, acc_device_t devtype  ){
    if(devtype==acc_device_nvcuda){
#ifdef __NVCUDA__
        fprintf(stderr,"Device partitioning is not supported on CUDA\n");
        exit(-1);
#endif 
    }else if(devtype==acc_device_nvocl || devtype==acc_device_intelocl){
#ifdef __NVOPENCL12__
        cl_device_id *device_to_partition=device;
        unsigned int ncore_per_partition=0;
        sscanf(getenv("IPMACC_DEVICE_PART"),"%u",&ncore_per_partition);
        assert(ncore_per_partition>0);
        int i;
        cl_device_partition_property prop[]={CL_DEVICE_PARTITION_EQUALLY,ncore_per_partition,0};
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
    //printf("HAH<\n");
    acc_set_device_type(devtype);
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
        //__ipmacc_devicetype=devtype;//acc_device_nvcuda;
    }else if(devtype==acc_device_nvocl || devtype==acc_device_intelocl){
#ifdef __NVOPENCL__
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
        cl_int error;

        /////////////////////
        // SELECT PLATFORM //
        /////////////////////
        char * platform_name ;
        cl_context   *platform_context ;  //  per platform
        cl_device_id **platform_devices ; // per platform list of device
        int *platform_deviceCount, **platform_device_computeunit_counts ;
        size_t platform_name_size ;
        // get all platforms
        clGetPlatformIDs(0, NULL, &platformCount);
        platforms = (cl_platform_id*) malloc(sizeof(cl_platform_id) * platformCount);
        clGetPlatformIDs(platformCount, platforms, NULL);
        platform_context=(cl_context*)malloc(sizeof(cl_context)*platformCount);
        platform_devices=(cl_device_id**)malloc(sizeof(cl_device_id*)*platformCount);
        platform_deviceCount=(int*)malloc(sizeof(int)*platformCount);
        platform_device_computeunit_counts=(int**)malloc(sizeof(int*)*platformCount);
        // get list of devices in each platform
        int selected_platformID=0;// select the platform of intend
        char *selected_platformName=NULL;
        char *env_acc_device_type = getenv("ACC_DEVICE_TYPE");
        short use_env = env_acc_device_type!=NULL;
        for (i = 0; i < platformCount; i++) {
            clGetPlatformInfo(platforms[i],CL_PLATFORM_NAME, 0, NULL, &platform_name_size);
            platform_name = (char *)malloc(sizeof(char)*platform_name_size);
            clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, platform_name_size, platform_name, NULL);
            if (getenv("IPMACCLIB_VERBOSE")) printf("platform name: %s\n", platform_name);
            // set the platform
            if(use_env){
                // give higher priority to environment variable
                if(strcmp(env_acc_device_type,platform_name)==0){
                    selected_platformID=i;
                    selected_platformName=platform_name;
                }
            }else{
                switch(devtype){
                    case acc_device_nvocl:
                        if(strcmp(platform_name,"NVIDIA CUDA")==0){
                            selected_platformID=i;
                            selected_platformName=platform_name;
                        }
                        break;
                    case acc_device_intelocl:
                        if(strcmp(platform_name,"Intel(R) OpenCL")==0){
                            selected_platformID=i;
                            selected_platformName=platform_name;
                        }
                        break;
                    default:
                        break;
                }
            }

            // get all devices
            clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_DEFAULT, 0, NULL, &deviceCount);
            devices = (cl_device_id*) malloc(sizeof(cl_device_id) * deviceCount);
            clGetDeviceIDs(platforms[i], CL_DEVICE_TYPE_DEFAULT, deviceCount, devices, NULL);
            platform_devices[i]=devices;
            platform_deviceCount[i]=deviceCount;
            platform_device_computeunit_counts[i]=(int*)malloc(sizeof(int)*deviceCount);

            // print the device names
            for (j = 0; j < deviceCount; j++)
            {
                // print device name
                clGetDeviceInfo(devices[j], CL_DEVICE_NAME, 0, NULL, &valueSize);
                value = (char*) malloc(valueSize);
                clGetDeviceInfo(devices[j], CL_DEVICE_NAME, valueSize, value, NULL);
                if (getenv("IPMACCLIB_VERBOSE")) printf("%d. Device: %s\n", j+1, value);
                free(value);
                clGetDeviceInfo(devices[j],
                        CL_DEVICE_MAX_COMPUTE_UNITS,
                        sizeof(platform_device_computeunit_counts[i][j]),
                        &platform_device_computeunit_counts[i][j],
                        NULL);
                if (getenv("IPMACCLIB_VERBOSE")) printf("%d.  Max Compute Units: %d\n", j+1, platform_device_computeunit_counts[i][j]);
            }

            // create context on this platform (root device)
            error = CL_SUCCESS;
            platform_context[i]=clCreateContext( NULL, // context properties
                    deviceCount, platform_devices[i],
                    NULL, // call back
                    NULL, // user data to call back
                    &error);
            if(error!=CL_SUCCESS){
                printf("Error in clCreateContext();\n");
            }
        }
        if(selected_platformName==NULL){
            // exit, as there is no platfor as requested by the user.
            printf("Unable to find the requested device type\n");
            printf("[1] ACC_DEVICE_TYPE environment variable> \"%s\" [availables are ", env_acc_device_type);
            for (i = 0; i < platformCount; i++) {
                clGetPlatformInfo(platforms[i],CL_PLATFORM_NAME, 0, NULL, &platform_name_size);
                platform_name = (char *)malloc(sizeof(char)*platform_name_size);
                clGetPlatformInfo(platforms[i], CL_PLATFORM_NAME, platform_name_size, platform_name, NULL);
                printf("\"%s\" ", platform_name);
            }
            printf("]\n");
            printf("[2] acc_device_t passed to acc_init()> ");
            switch(devtype){
                case acc_device_nvocl:
                    printf("acc_device_nvocl");
                    break;
                case acc_device_intelocl:
                    printf("acc_device_intelocl");
                    break;
                default:
                    break;
            }
            printf(" [availables are acc_device_nvocl acc_device_intelocl]\n");
            printf("aborting()\n");
            exit(-1);
        }
        if (getenv("IPMACC_VERBOSE")){
            printf("Selected Platform Name: %s\n", selected_platformName);
        }

        ///////////////////
        // SELECT DEVICE //
        ///////////////////
        char *env_acc_device_num = getenv("ACC_DEVICE_NUM");
        int selected_deviceID=0;  // select a device in the platform of intend
        if(env_acc_device_num==NULL){
            // pick the first device
            selected_deviceID = 0;
        }else{
            selected_deviceID = atoi(env_acc_device_num); // if fails, picks 0
            if(selected_deviceID>=platform_deviceCount[selected_platformID] || selected_deviceID<0){
                printf("invalid device ID requested from platform %s: %d\n", selected_platformName, selected_deviceID);
                printf("[1] ACC_DEVICE_NUM environment variable> %s [availables are ", env_acc_device_num);
                for(i=0; i<platform_deviceCount[selected_platformID]; i++){
                    printf("\"%d\" ",i);
                }
                printf("]\n");
                printf("[2] acc_set_device_num> %d [unimplemented]\n", 0);
                printf("aborting()\n");
                exit(-1);
            }
        }
        int selected_n_computeUnits=platform_device_computeunit_counts[selected_platformID][selected_deviceID]; // number of compute units in the selected device

        cl_device_id device_id = platform_devices[selected_platformID][selected_deviceID];
        // OLD CODE FOR FINDING AN OPENCL DEVICE:
        /*
        //cl_platform_id platform_id = NULL;
        //cl_uint ret_num_devices;
        //cl_uint ret_num_platforms;
        //__ipmacc_clerr = clGetPlatformIDs(1, &platform_id, &ret_num_platforms);
        //if(__ipmacc_clerr!=CL_SUCCESS){
        //    printf("Runtime error! unable to find any OpenCL-enabled platform\n");
        //    printf("Check the installation of system OpenCL driver\n");
        //    exit(-1);
        //}
        //__ipmacc_clerr = clGetDeviceIDs( platform_id, CL_DEVICE_TYPE_DEFAULT, 1, &device_id, &ret_num_devices);
        //if(__ipmacc_clerr!=CL_SUCCESS){
        //    printf("Runtime error! unable to retrieve the device id of CL_DEVICE_TYPE_DEFAULT\n");
        //    exit(-1);
        //}
        // */
        // select device
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
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
        }else{
#ifdef __NVOPENCL12__ 
            // dynamic device partitioning
            // 2.I 
            // find the number of possible partitionings
            unsigned int n_partitioning=0; // number of ways that device can be partitioned equally
            for(i=2; i<selected_n_computeUnits; i=i<<1){
                if((selected_n_computeUnits%i)==0){
                    n_partitioning++;
                }
            }
            if (getenv("IPMACCLIB_VERBOSE")) printf("Device can be partitioned in %d different ways. \n",n_partitioning);

            // Following variables are allocated one per partitioning type (on the selected platform)
            //  list of subdevices in every partitioning type
            //  list of contexts on devices
            unsigned int current_partitioning=0; // always lower than n_partitioning

            // unified context
            cl_context unified_context;
            cl_device_id *unified_context_device_list=(cl_device_id*)malloc(sizeof(cl_device_id)*n_partitioning);
            // 2.II perform possible partitioing and 
            // pick the first device in each partitioinig type and
            // push it to the unified_context_device_list
            //
            for(i=2; i<selected_n_computeUnits; i=i<<1){
                if((selected_n_computeUnits%i)!=0){
                    continue;
                }
                assert(n_partitioning>current_partitioning);
                // partition the first device of first platform into 1/16, 1/8, 1/4, 1/2
                const cl_device_partition_property prop[]={CL_DEVICE_PARTITION_EQUALLY,i,0};
                cl_uint subdeviceCount_g=selected_n_computeUnits/i; // the number of sub-devices
                cl_uint subdeviceCount_r=-1;
                cl_device_id *subdevices=(cl_device_id*)malloc(sizeof(cl_device_id)*subdeviceCount_g);
                error=clCreateSubDevices(platform_devices[selected_platformID][selected_deviceID],
                        prop, subdeviceCount_g,
                        subdevices,
                        &subdeviceCount_r);
                if(subdevices==NULL || subdeviceCount_r==-1){
                    printf("\t failed to parition the device: error %d\n",error);
                }else if (getenv("IPMACCLIB_VERBOSE")) {
                    printf("\t root device is partitioned into %d subdevices\n",
                            subdeviceCount_r);
                    printf("\t root device id: %u\n\t\tpartitioning #%d (%d cores, %d subdevices): ",
                            platform_devices[selected_platformID][selected_deviceID],
                            current_partitioning,i,selected_n_computeUnits/i);
                    for(j=0; j<subdeviceCount_r; j++)
                        printf("%u, ",subdevices[j]);
                    printf("\n");
                }
                unified_context_device_list[current_partitioning]=subdevices[0];
                current_partitioning++;
            }
            unified_context = clCreateContext(NULL,
                    n_partitioning, unified_context_device_list,
                    NULL, NULL, &error);
            if(error!=CL_SUCCESS){
                printf("\t\tfailed to create the unified context! error# %d\n",error);
            }else if (getenv("IPMACCLIB_VERBOSE")) {
                printf("\t\tunified context [created]\n");
            }
            __ipmacc_clctx=unified_context;
            __ipmacc_cldevs=unified_context_device_list;
            __ipmacc_clnpartition=n_partitioning;

            // 2.III create command-queue per partitioning
            __ipmacc_clpartitions_command_queues=(cl_command_queue*)malloc(sizeof(cl_command_queue)*__ipmacc_clnpartition);
            for(i=0; i<__ipmacc_clnpartition; i++){
                __ipmacc_clpartitions_command_queues[i] = clCreateCommandQueue(__ipmacc_clctx, __ipmacc_cldevs[i], 0, &__ipmacc_clerr);
                if(__ipmacc_clerr!=CL_SUCCESS){
                    printf("\t\tfailed to command-queue on the partitioning #%d! error# %d\n", i, error);
                    exit(-1);
                }else if (getenv("IPMACCLIB_VERBOSE")) {
                    printf("\t\tcommand-queue on partitioining #%d [created]\n",i);
                }
            }
#endif 
        }
        //__ipmacc_devicetype=device_type;//acc_device_nvocl;
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_shutdown( acc_device_t devtype ){

    if(getenv("IPMACC_VERBOSE")) printf("IPMACC: [shutting down the accelerator!]\n");
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
        //	}else if(devtype==acc_device_nvocl){
        //#ifdef __NVOPENCL__

        //#endif 
}else{
    fprintf(stderr,"Unimplemented device type!\n");
    exit(-1);
}
}


// int acc_on_device( acc_device_t devtype );
void* acc_malloc(size_t bytes){
    // allocate space on device and return the pointer
    // no need to associate the pointer with a host pointer
    if(__ipmacc_devicetype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        void *ptr=NULL;
        cudaError_t err=cudaSuccess;
        err=cudaMalloc((void**)&ptr,bytes);
        if(err!=cudaSuccess){
            printf("failed to allocate memory %16llu bytes on CUDA device by acc_malloc: error-code (%d)\n", bytes, err);
            exit(-1);
        }else if(getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [allocated] on device by acc_malloc (ptr: %p)\n",bytes,ptr);
        return ptr;
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        void *ptr=(void*)clCreateBuffer(__ipmacc_clctx, CL_MEM_READ_WRITE, bytes, NULL, &__ipmacc_clerr);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("failed to allocate memory %16llu bytes on OpenCL device by acc_malloc: %d\n", bytes, __ipmacc_clerr);
            exit(-1);
        }else{
            if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [allocated] on device by acc_malloc (ptr: %p)\n",bytes,ptr);
        }
        return ptr;
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_free(void *d_ptr){
    // free the device memory.
    // d_ptr should be allocated by acc_malloc
    if(__ipmacc_devicetype==acc_device_nvcuda){
        //CUDA on NV
#ifdef __NVCUDA__
        cudaError_t err = cudaFree(d_ptr);
        if(err!=cudaSuccess){
            printf("failed to release memory pointer (%p) on CUDA device by acc_free: error-code (%d)\n", d_ptr, err);
            exit(-1);
        }
#endif 
        //}else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){\
        // could not find proper API in OpenCL \
#ifdef __NVOPENCL__\
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
        // outsourced from http://gpucoder.livejournal.com/1064.html
        int devCount;
        cudaGetDeviceCount(&devCount);
        printf("CUDA Device Query...\n");
        printf("There are %d CUDA devices.\n", devCount);

        // Iterate through devices
        int i, j;
        for (i = 0; i < devCount; ++i)
        {
            // Get device properties
            printf("\nCUDA Device #%d\n", i);
            struct cudaDeviceProp devProp;
            cudaGetDeviceProperties(&devProp, i);
            printf("\tMajor revision number:         %d\n",  devProp.major);
            printf("\tMinor revision number:         %d\n",  devProp.minor);
            printf("\tName:                          %s\n",  devProp.name);
            printf("\tTotal global memory:           %u\n",  devProp.totalGlobalMem);
            printf("\tTotal shared memory per block: %u\n",  devProp.sharedMemPerBlock);
            printf("\tTotal registers per block:     %d\n",  devProp.regsPerBlock);
            printf("\tWarp size:                     %d\n",  devProp.warpSize);
            printf("\tMaximum memory pitch:          %u\n",  devProp.memPitch);
            printf("\tMaximum threads per block:     %d\n",  devProp.maxThreadsPerBlock);
            for (j = 0; j < 3; ++j){
                printf("\tMaximum dimension %d of block:  %d\n", j, devProp.maxThreadsDim[j]);
            }
            for (j = 0; j < 3; ++j){
                printf("\tMaximum dimension %d of grid:   %d\n", j, devProp.maxGridSize[j]);
            }
            printf("\tClock rate:                    %d\n",  devProp.clockRate);
            printf("\tTotal constant memory:         %u\n",  devProp.totalConstMem);
            printf("\tTexture alignment:             %u\n",  devProp.textureAlignment);
            printf("\tConcurrent copy and execution: %s\n",  (devProp.deviceOverlap ? "Yes" : "No"));
            printf("\tNumber of multiprocessors:     %d\n",  devProp.multiProcessorCount);
            printf("\tKernel execution timeout:      %s\n",  (devProp.kernelExecTimeoutEnabled ? "Yes" : "No"));
        }
#endif 
    }else if(devtype==acc_device_nvocl || devtype==acc_device_intelocl){
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
        size_t platform_name_size ;
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
void* acc_compress_create(void* hostptr, size_t bytes,char* datatypestring,__constant__ void* const_mem_coef, int isRangeGiven, double min, double max){
    void *devptr=NULL;
    int compRatio=2;
    bytes=bytes/compRatio;
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        cudaError_t err=cudaMalloc((void**)&devptr,bytes);
        if(err!=cudaSuccess){
            printf("failed to allocate memory %16llu bytes on CUDA device: %d\n", bytes, err);
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
    openacc_ipmacc_varmapper_t* obj=openacc_ipmacc_get_object(hostptr); 
    switch (datatypestring[0]){
        case 'd':
            obj->type='d';
            break;
        case 'f':
            obj->type='f';
            break;
    }
    obj->compRatio=compRatio;
    if(isRangeGiven==0){
        if(strcmp(datatypestring,"double")==0){
            double coef [3];
            if(fabs(max)>fabs(min)){
                coef[0] = 2*fabs(max)+fabs(max)/100;
                coef[1] = -3*fabs(max)-3*fabs(max)/200;
                //coef = fabs(max)+fabs(max)/1000;
            }else{
                coef[0] = 2*fabs(min)+fabs(min)/100;
                coef[1] = -3*fabs(min)-3*fabs(min)/200;
                //coef = fabs(min)+fabs(min)/1000;
            }
            coef[2]=1.0/coef[0];
            obj->dcoef1=coef[0];
            obj->dcoef2=coef[1];
            cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,3*sizeof(double),0,cudaMemcpyHostToDevice);
        }else if(strcmp(datatypestring,"float")==0){
            float coef [3];
            if(fabs(max)>fabs(min)){
                coef[0] = 2*fabs(max)+fabs(max)/100;
                coef[1] = -3*fabs(max)-3*fabs(max)/200;
                //coef = fabs(max)+fabs(max)/1000;
            }else{
                coef[0] = 2*fabs(min)+fabs(min)/100;
                coef[1] = -3*fabs(min)-3*fabs(min)/200;
                //coef = fabs(min)+fabs(min)/1000;
            }
            coef[2]=1.0/coef[0];
            obj->fcoef1=coef[0];
            obj->fcoef2=coef[1];
            cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,3*sizeof(float),0,cudaMemcpyHostToDevice);
        }
    }

#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: create devpointer %p\n",devptr);
#endif
    return devptr;
}
void* acc_create( void* hostptr, size_t bytes )
{
    void *devptr=NULL;
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        cudaError_t err=cudaMalloc((void**)&devptr,bytes);
        if(err!=cudaSuccess){
            printf("failed to allocate memory %16llu bytes on CUDA device: error-code (%d)\n", bytes, err);
            exit(-1);
        }else if(getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [allocated] on device (ptr: %p)\n",bytes,devptr);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        devptr=(void*)clCreateBuffer(__ipmacc_clctx, CL_MEM_READ_WRITE, bytes, NULL, &__ipmacc_clerr);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("failed to allocate memory %16llu bytes on OpenCL device: %d\n", bytes, __ipmacc_clerr);
            exit(-1);
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
void* acc_compress_present_or_create ( void* hostptr, size_t bytes, char* datatypestring, void* const_mem_coef, int isRangeGiven, double min, double max)
{
    void *devptr=acc_deviceptr(hostptr);
    if(devptr){
        return devptr ;
    }else{
        devptr = acc_compress_create(hostptr, bytes, datatypestring, const_mem_coef, isRangeGiven, min, max);
    }
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: create devpointer %p\n",devptr);
#endif
    return devptr;
}
void* acc_present_or_create ( void* hostptr, size_t bytes)
{
    void *devptr=acc_deviceptr(hostptr);
    if (getenv("IPMACCLIB_VERBOSE")){
        printf("Looking up address on device (hostptr: %p devptr: %p)\n", hostptr, devptr);
    }

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
    //copyout
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyout devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes,devptr);
        cudaMemcpy(hostptr, devptr, bytes, cudaMemcpyDeviceToHost);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueReadBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("Runtime error! Cannot read buffer from device: #%d\n",err);
            exit(-1);
        }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_copyout_to_comp ( void * hostptr, size_t bytes)
{
    // copy the data from device back to host
    void* devptr=acc_deviceptr(hostptr);
    if(devptr==NULL){
        printf("Data is not found on the device!\n");
        exit(-1);
    }
    //copyout
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyout devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes,devptr);
        printf("comp pointer out:%p\n",openacc_ipmacc_get_comp(hostptr));
        cudaMemcpy(openacc_ipmacc_get_comp(hostptr), devptr, bytes, cudaMemcpyDeviceToHost);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueReadBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("Runtime error! Cannot read buffer from device: #%d\n",err);
            exit(-1);
        }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_delete ( void*hostptr, size_t bytes)
{
    // first assert it exist on accelerator
    // then free the accelerator memory associated with this hostptr
    void *deviceptr = openacc_ipmacc_unmap_memory(hostptr);
    if(deviceptr==NULL){
        fprintf(stderr,"OpenACC Runtime Error in acc_delete\n");
        fprintf(stderr,"No memory is associated with the given pointer on the accelerator memory! [hostptr: %p]\n",hostptr);
        fprintf(stderr,"aborting\n");
        exit(-1);
    }
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        cudaError_t err = cudaFree(deviceptr);
        if(err!=cudaSuccess){
            printf("failed to release memory pointer (%p) on CUDA device by acc_free: error-code (%d)\n", deviceptr, err);
            exit(-1);
        }
#endif 
        //}else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){\
        // no OpenCL API found to allow releasing the memory \
#ifdef __NVOPENCL__ \
#endif
}else{
    fprintf(stderr,"Unimplemented device type!\n");
    exit(-1);
}
//return openacc_ipmacc_get(hostptr);
}   
void acc_copyout ( void* hostptr, size_t bytes )
{
    // copyout_keep
    acc_copyout_and_keep ( hostptr, bytes);

    // delete
    acc_delete(hostptr, bytes);
}
void decompression(void* hostptr, size_t bytes){
    struct openacc_ipmacc_varmapper_s* obj=openacc_ipmacc_get_object(hostptr); 
    if(obj->type=='f'){
        if(obj->compRatio==2){
            int i;
            float coef[3];
            coef[0]=obj->fcoef1;
            coef[1]=obj->fcoef2;
            for(i = 0; i< bytes/sizeof(float); i++){
                unsigned int temp;
                temp=((unsigned short*)obj->src_comp)[i];
                //if(i<10)printf("before: %f\n",((float*)(obj->src_comp))[i]);
                temp=temp<<7;
                temp=temp | 0x3F800000;
                ((float*)hostptr)[i] = ((*((float*)&temp)*coef[0]+coef[1]));
                //if(i<10)printf("%f\n",((float*)hostptr)[i]);
            }
        }
    }else if(obj->type=='d'){
        if(obj->compRatio==2){
            int i;
            double coef[2];
            coef[0]=obj->dcoef1;
            coef[1]=obj->dcoef2;
            //printf("1:%f 2:%f\n",coef[0],coef[1]);
            //printf("pointer:%p\n",obj->src_comp);
            for(i = 0; i< bytes/sizeof(double); i++){
                unsigned long long temp;
                temp=((unsigned int*)obj->src_comp)[i];
                //if(i<10)printf("before: %f\n",((float*)(obj->src_comp))[i]);
                temp=temp<<20;
                temp=temp | 0x3FF0000000080000;
                //if(i<10)printf("temp:%d\n",temp);
                ((double*)hostptr)[i] = ((*((double*)&temp)*coef[0]+coef[1]));
                //if(i<10)printf("%f\n",((double*)hostptr)[i]);
            }
        }
    }
}
void acc_decompress_copyout ( void* hostptr, size_t bytes )
{
    int compRatio=2;
    if(openacc_ipmacc_get_comp(hostptr)==NULL){
        openacc_ipmacc_set_comp(hostptr, malloc(bytes/compRatio));
    }
    // copyout_keep
    acc_copyout_to_comp ( hostptr, bytes/compRatio);
    decompression(hostptr, bytes);

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
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyin]    from device (ptr: %p)\n",bytes,devptr);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueWriteBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("Runtime error! Cannot write buffer to device: #%d\n",err);
            exit(-1);
        }

#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
    return devptr ;
} 

void* acc_copy_from_compressed( void* hostptr, void* compSrc, size_t bytes )
{
    void* devptr=acc_deviceptr(hostptr);

    //copyin
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyin devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyin]    to device (ptr: %p)\n",bytes,devptr);
        cudaMemcpy(devptr, compSrc, bytes, cudaMemcpyHostToDevice); 
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyin]    from device (ptr: %p)\n",bytes,devptr);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueWriteBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, compSrc, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("Runtime error! Cannot read buffer from device: #%d\n",err);
            exit(-1);
        }

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
void*  compression(void* hostPtr, void* devPtr, size_t bytes, char* datatypestring, __constant__ void* const_mem_coef, int compRatio, int itemNum, int isReadOnly, float inMin, float inMax){
    void* compPtr=NULL;
    int j;
#ifdef TIMING
    for(j=0;j<1;j++){
        gettimeofday(&t1, NULL);
#endif
        openacc_ipmacc_varmapper_t* obj=openacc_ipmacc_get_object(hostPtr); 
        if (!strcmp(datatypestring,"float")){
            if(compRatio==2) {
                float temp, max, min;
                float coef [2];
                float *fptr = hostPtr;
                unsigned short *shortCompPtr = (unsigned short *)malloc(bytes/compRatio);
                int i;
                if(isReadOnly){
                    max=fptr[0];
                    min=fptr[0];
                    for( i = 0 ; i < bytes/sizeof(float); i++){
                        if(max<fptr[i]){
                            max=fptr[i];
                        }else{
                            min=(min>=fptr[i]?fptr[i]:min);
                        }
                        //max=(max<fptr[i]?fptr[i]:max);
                        //min=(min>=fptr[i]?fptr[i]:min);
                    }
                }else{
                    min=inMin;
                    max=inMax;
                }
                if(fabs(max)>fabs(min)){
                    coef[0] = 2*fabs(max)+fabs(max)/(float)100;
                    coef[1] = -3*fabs(max)-3*fabs(max)/(float)200;
                    //coef = fabs(max)+fabs(max)/1000;
                }else{
                    coef[0] = 2*fabs(min)+fabs(min)/(float)100;
                    coef[1] = -3*fabs(min)-3*fabs(min)/(float)200;
                    //coef = fabs(min)+fabs(min)/1000;
                }
                coef[2]=1/coef[0];
                obj->fcoef1=coef[0];
                obj->fcoef2=coef[1];
                obj->type='f';
                obj->compRatio=2;
                obj->src_comp=shortCompPtr;
                cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,3*sizeof(float),0,cudaMemcpyHostToDevice);

                if(err!=cudaSuccess){
                    printf("const memory error.(error code: %d)\n",err);
                }

                /*        void* tempDevPtr; 
                          cudaError_t err=cudaMalloc((void**)&tempDevPtr,bytes);
                          cudaMemcpy(hostptr, tempDevPtr, bytes, cudaMemcpyHostToDevice);
                          float_compress<<<abs(bytes/sizeof(float))/256,256>>>(tempDevPtr,devPtr,bytes/sizeof(float));
                          */
                unsigned int inttemp;
                unsigned int a = 0x3FBFFFFF ;
                unsigned int b = 0x3FC00080 ;
                for ( i = 0; i < bytes/sizeof(float); i++) {
                    temp = ((fptr[i])/coef[0]); // -0.5<temp<0.5
                    float ebad=temp+(float)1.5;
                    /* This code segment keeps the sign of the numbers after compression.
                     *
                     unsigned int c = (*(unsigned int*)&(ebad))&0xFFFFFF80;
                     if (temp<0 & ((ebad)==1.5)){temp=*(float*)&a ;}
                     else if (temp>0 & ((ebad)==1.5)){temp=*(float*)&b ;}
                     else if((*(float*)&c)==1.5&&ebad!=1.5){temp=*(float*)&b;}
                     else{temp=ebad;}
                     */
                    temp = ebad;
                    //temp += 1.5; // 1<temp<2
                    shortCompPtr[i] = ((*((unsigned int*)&temp))>>7)&0x0000FFFF;
                    //if(i<10)printf("%f\n",fptr[i]);
                    /* This code segment prints the number before compression and after decompression. 
                       inttemp=(shortCompPtr)[i];
                       inttemp=inttemp<<7;
                       inttemp=inttemp|0x3F800000;
                       if(((*((float*)&(inttemp))-1.5)* coef )<=0)
                       printf("org: %.10f, aftar decomp: %.10f, temp: %.10f\n",fptr[i], ((*((float*)&(inttemp))-1.5)* coef ),temp);
                       */
                    /*if(fptr[i]>0){
                      temp = ((fptr[i]+coef)/coef);
                      shortCompPtr[i] = ((*((unsigned int*)&temp))>>8)&0x00007FFF;
                      inttemp=(shortCompPtr)[i];
                      inttemp=inttemp<<16;
                      inttemp=inttemp>>8;
                      inttemp=inttemp&0x807FFFFF;
                      inttemp=inttemp|0x3F800040;
                      printf("org: %f, aftar decomp: %f\n", (*((float*)&(inttemp))* coef -coef), fptr[i]);
                      }else{
                      temp = ((fptr[i]+coef)/coef);
                      shortCompPtr[i] = (((*((unsigned int*)&temp))>>8)&0x0000FFFF)|0x00008000;
                      }*/
                }

                compPtr=(void*)shortCompPtr;
            }else if(compRatio==4){
                float temp, max;
                float *fptr = hostPtr;
                unsigned char *shortCompPtr = (unsigned char *)malloc(bytes/4);
                int i;
                for( i = 0 ; i < bytes/sizeof(float); i++){
                    max=(max<fptr[i]?fptr[i]:max);
                }
                max+=max/100;
                //printf("max: %f\n", max);
                cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,&max,sizeof(float),0,cudaMemcpyHostToDevice);

                if(err!=cudaSuccess){
                    printf("const memory error.(error code: %d)\n",err);
                }

                for ( i = 0; i < bytes/sizeof(float); i++) {
                    temp = ((fptr[i]+max)/max);
                    shortCompPtr[i] =((*((unsigned int*)&temp))>>15)&0x000000FF;
                }
                compPtr=(void*)shortCompPtr;
            }
        }else if (!strcmp(datatypestring,"double")){
            double temp, max, min;
            double coef[3];
            double *dptr = hostPtr;
            if(compRatio==2){
                unsigned int *intCompPtr = (unsigned *)malloc(bytes/compRatio);
                int i;
                if(isReadOnly){
                    max = dptr[0];
                    min = dptr[0];
                    for( i = 0 ; i < bytes/sizeof(double); i++){
                        if(max<dptr[i]){
                            max=dptr[i];
                        }else{
                            min=(min>=dptr[i]?dptr[i]:min);
                        }
                    }
                }else{
                    min=inMin;
                    max=inMax;
                }
                if(fabs(max)>fabs(min)){
                    coef[0] = 2*fabs(max)+fabs(max)/100;
                    coef[1] = -3*fabs(max)-3*fabs(max)/200;
                    //coef = fabs(max)+fabs(max)/1000;
                }else{
                    coef[0] = 2*fabs(min)+fabs(min)/100;
                    coef[1] = -3*fabs(min)-3*fabs(min)/200;
                    //coef = fabs(min)+fabs(min)/1000;
                }
                coef[2]=1.0/coef[0];
                //printf("1:%f 2:%f 3:%f\n" ,coef[0],coef[1],coef[2]);
                obj->dcoef1=coef[0];
                obj->dcoef2=coef[1];
                obj->type='d';
                obj->compRatio=2;
                cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,3*sizeof(double),0,cudaMemcpyHostToDevice);

                if(err!=cudaSuccess){
                    printf("const memory error.(error code: %d)\n",err);
                }

                for ( i = 0; i < bytes/sizeof(double); i++) {
                    temp = (dptr[i]/coef[0])+1.5;
                    intCompPtr[i] =((*((unsigned long long*)&temp))>>20)&0x00000000FFFFFFFF;
                    //if(i<10)printf("%f\n",dptr[i]);
                }
                compPtr=(void*)intCompPtr;
            }else if(compRatio==4){
                unsigned short *intCompPtr = (unsigned short *)malloc(bytes/compRatio);
                int i;
                for( i = 0 ; i < bytes/sizeof(double); i++){
                    max = dptr[0];
                    min = dptr[0];
                    if(max<dptr[i]){
                        max=dptr[i];
                    }else{
                        min=(min>=dptr[i]?dptr[i]:min);
                    }
                }
                if(fabs(max)>fabs(min)){
                    coef[0] = 2*fabs(max)+fabs(max)/100;
                    coef[1] = -3*fabs(max)-3*fabs(max)/200;
                    //coef = fabs(max)+fabs(max)/1000;
                }else{
                    coef[0] = 2*fabs(min)+fabs(min)/100;
                    coef[1] = -3*fabs(min)-3*fabs(min)/200;
                    //coef = fabs(min)+fabs(min)/1000;
                }
                cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,2*sizeof(double),0,cudaMemcpyHostToDevice);

                if(err!=cudaSuccess){
                    printf("const memory error.(error code: %d)\n",err);
                }

                for ( i = 0; i < bytes/sizeof(double); i++) {
                    temp = (dptr[i]/coef[0])+1.5;
                    intCompPtr[i] =((*((unsigned long long*)&temp))>>36)&0x000000000000FFFF;
                }
                compPtr=(void*)intCompPtr;
            }
        }else if (!strcmp(datatypestring,"struct")){ 
            float temp, max, min;
            float *fptr = hostPtr;
            float coef[2];
            unsigned short *shortCompPtr = (unsigned short *)malloc(bytes/2);
            int i;

            for( i = 0 ; i < bytes/sizeof(float); i++){
                if(max<fptr[i]){
                    max=fptr[i];
                }else{
                    min=(min>=fptr[i]?fptr[i]:min);
                }
                //max=(max<fptr[i]?fptr[i]:max);
                //min=(min>=fptr[i]?fptr[i]:min);
            }

            if(fabs(max)>fabs(min)){
                coef[0] = 2*fabs(max)+fabs(max)/(float)100;
                coef[1] = -3*fabs(max)-3*fabs(max)/(float)200;
                //coef = fabs(max)+fabs(max)/1000;
            }else{
                coef[0] = 2*fabs(min)+fabs(min)/(float)100;
                coef[1] = -3*fabs(min)-3*fabs(min)/(float)200;
                //coef = fabs(min)+fabs(min)/1000;
            }
            cudaError_t err=cudaMemcpyToSymbol(const_mem_coef,coef,2*sizeof(float),0,cudaMemcpyHostToDevice);
            if(err!=cudaSuccess){
                printf("const memory error.(error code: %d)\n",err);
            }
            unsigned int objNum= bytes/(sizeof(float)*itemNum);
            for ( i = 0; i < objNum; i++) {
                for ( j = 0; j < itemNum ; j++) {
                    temp = ((fptr[i*itemNum+j])/coef[0]+1.5);
                    shortCompPtr[j*objNum+i] =((*((unsigned int*)&temp))>>7)&0x0000FFFF;
                }
            }
            compPtr=(void*)shortCompPtr;
        }
#ifdef TIMING
        gettimeofday(&t2, NULL);
        fprintf (stderr,"Total compression time = %f seconds\n",
                (double) (t2.tv_usec - t1.tv_usec) / 1000000 +
                (double) (t2.tv_sec - t1.tv_sec));
    }
#endif
    openacc_ipmacc_set_comp(hostPtr, compPtr);
    openacc_ipmacc_set_coef(hostPtr, const_mem_coef);
    return (void*)compPtr;
}
void* acc_compress_copyin( void* hostptr, size_t bytes, char* datatypestring, __constant__ void* const_mem_coef, int isReadOnly, float min, float max )
{
    int compRatio=2;
    int structItemNum=2;// It should be an input argument. Temprorarily stucked to 2 for testing on NN.
    struct timeval time1,time2;
    gettimeofday(&time1, NULL);

    void * devptr = acc_create( hostptr, bytes/compRatio );



    void * compPtr=compression(hostptr, devptr, bytes, datatypestring, const_mem_coef, compRatio, structItemNum, isReadOnly, min, max);
    if(compPtr!=NULL){
        void * tempPtr =  acc_copy_from_compressed(hostptr, compPtr, bytes/compRatio);
        gettimeofday(&time2, NULL);
        fprintf (stderr,"new time = %f seconds\n",
                (double) (time2.tv_usec - time1.tv_usec) / 1000000 +
                (double) (time2.tv_sec - time1.tv_sec));
        return tempPtr;
    }else{
        return acc_present_or_copyin(hostptr,bytes);
    }

}
void* acc_pcopyin ( void* hostptr , size_t bytes )
{
    return acc_present_or_copyin( hostptr, bytes);
}

void* acc_pcompress_copyin ( void* hostptr , size_t bytes, char * datatypestring , __constant__ void* const_mem_coef, int isReadOnly, float min, float max)
{
    int compRatio=2;
    int structItemNum=2;// It should be an input argument. Temprorarily stucked to 2 for testing on NN.
    void* devptr=acc_deviceptr(hostptr);
    if(devptr==NULL){
        //create
        printf("NULL devptr!\n");
        devptr = acc_create( hostptr, bytes/compRatio);
    }
    void* compPtr=compression(hostptr, devptr, bytes, datatypestring, const_mem_coef, compRatio, structItemNum, isReadOnly, min, max);
    if(compPtr!=NULL){
        return acc_copy_from_compressed(hostptr, compPtr, bytes/compRatio); 
    }else{
        return acc_present_or_copyin(hostptr,bytes);
    }
}
void acc_get_mem_info(size_t *free, size_t *total)
{
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        cudaError_t err=cudaMemGetInfo(free,total);
        if(err!=cudaSuccess){
            printf("failed to read device memory info! error-code (%d)\n", err);
            exit(-1);
        }
        //else if(getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [allocated] on device (ptr: %p)\n",bytes,devptr);
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        cl_ulong global_mem_size=0;
        clGetDeviceInfo(__ipmacc_cldevs[0], CL_DEVICE_GLOBAL_MEM_SIZE,
                sizeof(cl_ulong), &global_mem_size, NULL);
        total[0]=global_mem_size;
        free[0]=-1;
        printf("IPMACC: warning: cannot read the amount of free memory on this device!\n");
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("failed to read device memory info! error-code %d\n", __ipmacc_clerr);
            exit(-1);
        }
        //else{ \
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [allocated] on device (ptr: %p)\n",bytes,devptr); \
    }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_map_data( void *hostptr, void *deviceptr, size_t bytes)
{
    // halt if the hostptr is mapped to another deviceptr
    void *dptr = acc_deviceptr(hostptr  );
    void *hptr = acc_deviceptr(deviceptr);
    if(deviceptr==NULL || hostptr==NULL){
        fprintf(stderr,"OpenACC Runtime Error in acc_map_data\n");
        fprintf(stderr,"\teither host or accelerator pointer is NULL\n");
        fprintf(stderr,"aborting\n");
        exit(-1);
    }else if(dptr==deviceptr && hptr==hostptr){
        printf("warning: acc_map_data: pointers are already mapped!\n\tno further action is performed!\n");
    }else if(hptr==hostptr){
        fprintf(stderr,"OpenACC Runtime Error in acc_map_data \n");
        fprintf(stderr,"Given host pointer is already associated with an accelerator pointer! remap not allowed by OpenACC! [hostptr: %p]\n",hostptr);
        fprintf(stderr,"aborting\n");
        exit(-1);
    }else if(dptr==deviceptr){
        printf("warning: acc_map_data: device pointer is already mapped!\n\tadding second map and use it as the default!\n");
        openacc_ipmacc_insert(hostptr, deviceptr, bytes);
    }else{
        // normal append: adding a new mapping to list
        openacc_ipmacc_insert(hostptr, deviceptr, bytes);
    }

}
void acc_unmap_data( void *hostptr )
{
    // The acc_unmap_data routine is similar to an acc_delete
    // except the device memory is not deallocated.
    void *deviceptr = openacc_ipmacc_unmap_memory(hostptr);
    if(deviceptr==NULL){
        fprintf(stderr,"OpenACC Runtime Error in acc_unmap_data \n");
        fprintf(stderr,"No memory is associated with the given pointer on the accelerator memory! [hostptr: %p]\n",hostptr);
        fprintf(stderr,"aborting\n");
        exit(-1);
    }
}
void acc_memcpy_to_device( void* devptr, void* hostptr, size_t bytes )
{
    // assume hostptr and devptr are properly allocated and match in bytes.
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyin devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyin]    to device (ptr: %p)\n",bytes,devptr);
        cudaError_t err = cudaMemcpy(devptr, hostptr, bytes, cudaMemcpyHostToDevice); 
        if(err!=cudaSuccess){
            printf("OpenACC Runtime Error! acc_memcpy_to_device: Cannot copyin to device: #%d\n",err);
            exit(-1);
        }
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyin]    from device (ptr: %p)\n",bytes,devptr);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueWriteBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("OpenACC Runtime Error! acc_memcpy_to_device: Cannot write buffer to device: #%d\n",err);
            exit(-1);
        }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}
void acc_memcpy_from_device( void* hostptr, void* devptr, size_t bytes )
{
    // assume hostptr and devptr are properly allocated and match in bytes.
#ifdef DEBUG_LIB
    assert(devptr!=NULL);
    printf("ipmacc: copyout devpointer %p\n",devptr);
#endif
    if(__ipmacc_devicetype==acc_device_nvcuda){
#ifdef __NVCUDA__
        if (getenv("IPMACCLIB_VERBOSE")) printf("CUDA: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes,devptr);
        cudaError_t err=cudaMemcpy(hostptr, devptr, bytes, cudaMemcpyDeviceToHost);
        if(err!=cudaSuccess){
            printf("OpenACC Runtime Error! acc_memcpy_from_device: Cannot copyout from device: #%d\n",err);
            exit(-1);
        }
#endif 
    }else if(__ipmacc_devicetype==acc_device_nvocl || __ipmacc_devicetype==acc_device_intelocl){
#ifdef __NVOPENCL__
        if (getenv("IPMACCLIB_VERBOSE")) printf("OpenCL: %16llu bytes [copyout]   from device (ptr: %p)\n",bytes);
        cl_command_queue temp_queue=NULL;
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            temp_queue=__ipmacc_command_queue;
        }else{
            temp_queue=__ipmacc_clpartitions_command_queues[0];
        }
        cl_int err=clEnqueueReadBuffer(temp_queue, (cl_mem)devptr, CL_TRUE, 0, bytes, hostptr, 0, NULL, NULL);
        if(err!=CL_SUCCESS){
            printf("OpenACC Runtime error! acc_memcpy_from_device: Cannot read buffer from device: #%d\n",err);
            exit(-1);
        }
#endif
    }else{
        fprintf(stderr,"Unimplemented device type!\n");
        exit(-1);
    }
}




/////////////////////
// INTERNAL IPMACC //
// //////////////////


#ifdef __NVOPENCL__
/* TRAINING Wrappers:
 * only available in OpenCL */

// this structure keeps the track of all compiled kernels
typedef struct training_kernel_log_s {
    // gathered information
    double consumed_energy;
    double time_duration;
    unsigned int n_stalls;
    // configuration
    unsigned int n_core;
} training_kernel_log_t;
typedef struct training_kernel_s {
    cl_kernel obj;
    int id;
    const char *source;
    const char *cflags;
    int nargs;
    int ncalls;
    double consumed_energy;
    training_kernel_log_t *log;
    struct training_kernel_s *next;
} training_kernel_t;
// head of the list of the compiled kernels:
training_kernel_t *__ipmacc_outstanding_kernels=NULL;

// compiles and returns the OpenCL kernel object
// if the kernel is already compiled, just return the pointer
void* acc_training_kernel_add(const char *kernelSource, char *compileFlags, char *kernelName, int kernelId, int nargs)
{
    // check if it is already compiled
    training_kernel_t *p=__ipmacc_outstanding_kernels;
    while(p){
        if(p->id==kernelId){
            return p->obj; // kernel is compiled before
        }
        p=p->next;
    }
    // create program from source and
    // compile the program for every partitioining in the context and
    cl_program __ipmacc_clpgm0;
    __ipmacc_clpgm0=clCreateProgramWithSource(__ipmacc_clctx, 1, &kernelSource, NULL, &__ipmacc_clerr);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clCreateProgramWithSource! id: %d\n",__ipmacc_clerr);
        printf("have you forgot acc_init() in the begining of program?!\n");
        exit(-1);
    }
    char __ipmacc_clcompileflags0[128];
    sprintf(__ipmacc_clcompileflags0, compileFlags);
    __ipmacc_clerr
        =clBuildProgram(__ipmacc_clpgm0,
                0,
                NULL, // the third argument is null,
                // clBuildProgram compiles the program for all devices in the program context
                // in this case, for every individual partitioining types
                __ipmacc_clcompileflags0,
                NULL,
                NULL); 
    if(__ipmacc_clerr!=CL_SUCCESS){
        // if the compilations fails, return the compilation error
        printf("OpenCL Runtime Error in clBuildProgram! id: %d\n",__ipmacc_clerr);

        size_t log_size=1024;
        char *build_log=NULL;
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, 0, NULL, &log_size);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log = (char*)malloc((log_size+1));
        // Second call to get the log
        __ipmacc_clerr=clGetProgramBuildInfo(__ipmacc_clpgm0, __ipmacc_cldevs[0], CL_PROGRAM_BUILD_LOG, log_size, build_log, NULL);
        if(__ipmacc_clerr!=CL_SUCCESS){
            printf("OpenCL Runtime Error in clGetProgramBuildInfo! id: %d\n",__ipmacc_clerr);
        }
        build_log[log_size] = '\0';
        printf("--- Build log (%d) ---\n ",log_size);
        fprintf(stderr, "%s\n", build_log);
        free(build_log);
        exit(-1);
    }
    // append the kernel to the list of compiled kernels
    training_kernel_t *nodeToAppend=(training_kernel_t*)malloc(sizeof(training_kernel_t)*1);
    nodeToAppend->next=__ipmacc_outstanding_kernels;
    __ipmacc_outstanding_kernels=nodeToAppend;
    nodeToAppend->source=kernelSource;
    nodeToAppend->cflags=compileFlags;
    nodeToAppend->nargs=nargs;
    nodeToAppend->ncalls=0;
    nodeToAppend->id=kernelId;
    nodeToAppend->obj = clCreateKernel(__ipmacc_clpgm0, kernelName, &__ipmacc_clerr);
    if(__ipmacc_clerr!=CL_SUCCESS){
        printf("OpenCL Runtime Error in clCreateKernel! id: %d\n",__ipmacc_clerr);
        exit(-1);
    }
    // return the kernel
    return nodeToAppend->obj;
}

// based on the available gathered information
// decide the command-queue, or the number of cores,
// for executing the next launch of the kernel
void* acc_training_decide_command_queue(int kernelId)
{
    // update kernel statistics
    // if we are about to enqueue and execute a kernel,
    // it must be compiled before (by acc_training_kernel_add).
    // assert that it exists in the list
    training_kernel_t *p=__ipmacc_outstanding_kernels;
    while(p){
        if(p->id==kernelId){
            p->ncalls++;
            break;
        }
        p=p->next;
    }
    if(p==NULL){
        printf("IPMACC Fatal Error! Unable to find the kernelId! id: %d\n",kernelId);
        exit(-1);
    }else{
        // return the command queue
        if(getenv("IPMACC_DYNAMIC_DEVICE_PART")==NULL){
            return __ipmacc_command_queue;
        }else{
            // decide the command-queue for kernelId based
            // on the gathered information
            static int id=0;
            if(getenv("IPMACC_VERBOSE")) printf("[IPMACC] Selected command-queue: #%d\n",id);
            return __ipmacc_clpartitions_command_queues[(id++)%__ipmacc_clnpartition];
        }
    }
}

// this function will be called upon enqueuing a kernel
void *acc_training_kernel_start(int kernelId){
    __ipmacc_training_outstanding_kernel_id=kernelId;
    // start gathering information; energy, time, etc.
    /* HERE WE GO */

#ifdef RALP
    if(getenv("IPMACC_VERBOSE")){
        printf("[IPMACC] *************************************************************************\n");
        printf("[IPMACC] starting kernel training for kernel> %u\n",kernelId);
        getEnergy( &package0_before, &core0_before, PACKAGE0_CORE);
    }
    //getEnergy( &package1_before, &core8_before, PACKAGE1_CORE);
    //	printf("current energy for package#%d: %.6f\n", PACKAGE0, package0_before);
    //	printf("current energy for package#%d: %.6f\n", PACKAGE1, package1_before);
    //	printf("current energy for core#%d: %.6f\n", PACKAGE0_CORE, core0_before);
    //	printf("current energy for core#%d: %.6f\n", PACKAGE1_CORE, core8_before);
#endif
    // capturing the start time of the kernel
    gettimeofday(&t1, 0);
}



// this function will be called upon completion of a kernel
// notice: we only have one outstanding kernel launch and
// we keep the ID in __ipmacc_training_outstanding_kernel_id

void *acc_training_kernel_end(){
    assert(__ipmacc_training_outstanding_kernel_id!=-1);
    int kernelId=__ipmacc_training_outstanding_kernel_id;
    __ipmacc_training_outstanding_kernel_id=-1;

    // stop gathering information; energy, time, etc.
    // store counters
    /* HERE WE GO */

    training_kernel_t *p=__ipmacc_outstanding_kernels;
    cl_kernel obj=NULL;
    while(p){
        if(p->id==kernelId){
            obj=p->obj; // kernel is compiled before
            break;
        }
        p=p->next;
    }

#ifdef RALP
    // captuing energy at the end of kenel execution time
    getEnergy( &package0_after, &core0_after, PACKAGE0_CORE);
    //getEnergy( &package1_after, &core8_after, PACKAGE1_CORE);
    double consumed_energy = (package0_after - package0_before);// + (package1_after - package1_before);
    if(getenv("IPMACC_VERBOSE")) printf("[IPMACC] Consumed energy for kernel> %u: %.6f\n",kernelId, consumed_energy);
    // measuring consumed energy of the kernel
    p->consumed_energy = consumed_energy;

    /*
       /	printf("consumed energy for package#%d: %.6f\n", PACKAGE0, package0_after - package0_before);
       printf("consumed energy for package#%d: %.6f\n", PACKAGE1, package1_after - package1_before);
       printf("consumed energy for core#%d: %.6f\n", PACKAGE0_CORE, core0_after - core0_before);
       printf("consumed energy for core#%d: %.6f\n", PACKAGE1_CORE, core8_after - core8_before);
       */
#endif


    // capturing the end time of kernel
    gettimeofday(&t2, 0);

    double time = (1000000.0*(t2.tv_sec-t1.tv_sec) + t2.tv_usec-t1.tv_usec)/1000000.0;
    if(getenv("IPMACC_VERBOSE")){
        printf("[IPMACC] Execution-Time for kernel> %u : %f\n\n", kernelId, time);
        printf("[IPMACC] Ending kernel training for kernel> %u\n\n",kernelId);
        printf("[IPMACC] *************************************************************************\n");
    }

    // add the log to list: time, consumed_energy
    // FIXME

    return obj;
}


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


#endif // OPENCL Support

// PROFILER CODE
#define SILENT

struct timeval __ipmacc_internal_start, __ipmacc_internal_end;
double __ipmacc_internal_total_time[3] = {0.0, 0.0, 0.0};
// launch, execution, memory

void acc_profiler_start(){
    gettimeofday(&__ipmacc_internal_start, NULL);
}

void acc_profiler_end(int code){
    gettimeofday(&__ipmacc_internal_end, NULL);
    double delta = ((__ipmacc_internal_end.tv_sec  - __ipmacc_internal_start.tv_sec) * 1000000u +
            __ipmacc_internal_end.tv_usec - __ipmacc_internal_start.tv_usec) / 1.e6;
    __ipmacc_internal_total_time[code]+=delta;
#ifndef SILENT
    printf("<%s> %18.10fs\n",code==0?"Launch":(code==1?"Kernel":"Memory"),delta);
#endif
}

static char *rand_string(char *str, size_t size)
{
    const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJK";
    if (size) {
        --size;
        size_t n=0;
        for (n = 0; n < size; n++) {
            int key = rand() % (int) (sizeof charset - 1);
            str[n] = charset[key];
        }
        str[size] = '\0';
    }
    return str;
}
void acc_profiler_dump(){
    fprintf(stderr,"<%s> %18.10fs\n","kernel launch",   __ipmacc_internal_total_time[0]);
    fprintf(stderr,"<%s> %18.10fs\n","kernel execution",__ipmacc_internal_total_time[1]);
    fprintf(stderr,"<%s> %18.10fs\n","memory transfer", __ipmacc_internal_total_time[2]);
    struct timeval temp;
    gettimeofday(&temp, NULL);
    //char *prefix="profiler.";
    char *suffix=".txt";
    //char buffer[20]={"\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0"};
    char fname[30] = "profiler.";
    char randname[10];
    srand (time(NULL));
    rand_string(randname,10);
    //itoa((int)(__ipmacc_internal_end.tv_sec),buffer,10);
    //strcpy(fname,prefix);
    strcat(fname,randname);
    strcat(fname,suffix);
    printf("%s\n",fname);
    FILE *f=fopen(fname,"w");
    fprintf(f,"%18.10f %18.10f %18.10f\n",
            __ipmacc_internal_total_time[0],
            __ipmacc_internal_total_time[1],
            __ipmacc_internal_total_time[2]);
    fclose(f);
}

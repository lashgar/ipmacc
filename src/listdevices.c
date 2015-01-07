#include <string.h>
#include <stdio.h>
#include <assert.h>
#include "openacc.h"

int main(int argc, char *argv[]){
    unsigned int ocl=0;
    unsigned int cuda=0;
    if(argc!=2){
        printf("usage: ipmacc --list-devices <OCL|CUDA>\n");
        return -1;
    }else{
        ocl = (strcmp(argv[1],"OCL")==0);
        cuda= (strcmp(argv[1],"CUDA")==0);
        assert(ocl||cuda);
    }
    if(cuda){
        printf("spec of  CUDA-capable devices:\n");
        acc_list_devices_spec( acc_device_nvcuda);
    }
    if(ocl){
        printf("spec of OpenCL-capable devices:\n");
        acc_list_devices_spec( acc_device_nvocl);
    }
    return 0;
}

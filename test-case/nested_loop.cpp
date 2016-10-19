#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <iostream>
#include <malloc.h>
#include "openacc.h"

using namespace std;


int main(){
	int sum = 0 ;
	int sum2 = 0 ;
    int size1 = 16, size2 = 16, size3 = 16, size4=16;
    int total_iter = 32;
	int arr_size = (size1+total_iter)*(size2+total_iter)*(size3+total_iter);
	int *arr=(int*)malloc(sizeof(int)*arr_size);

    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 

	srand(time(NULL));

	for(int iter=0; iter<total_iter; ++iter)
	{
		sum = 0 ; 
		sum2 = 0 ; 
		for(int i = 0 ; i < size1*size2*size3; ++i)
		{
			arr[i] = rand()%100;
		}
	//	cout<<"enter input size"<<endl;
	//	cin>>arr_size;
		//#pragma acc loop independent vector(4) reduction(+:sum)
		#pragma acc kernels copy(arr[0:arr_size])
		#pragma acc loop independent vector(4) reduction(+:sum)
		for(int i = 0 ; i<size1; ++i){
		    #pragma acc loop independent vector(4)
            for(int j=0; j<size2; ++j){
                #pragma acc loop independent vector(4)
                for(int k=0; k<size3; ++k){
    			    sum += arr[i*size2*size3+j*size3+k];
                }
                #pragma acc loop independent vector(4)
                for(int k2=0; k2<size4; ++k2){
    			    float a = arr[i*size2*size3+j*size3+k2];
                }
            }
		}
		for(int i = 0 ; i < size1*size2*size3; ++i)
		{
			sum2 += arr[i];
		}
		cout<<"cpu result:"<<sum2<<endl;
		cout<<"gpu result:"<<sum<<endl;
		cout<<"array size:"<<arr_size<<endl;
        cout<<"size1:"<<size1<<endl;
        cout<<"size2:"<<size2<<endl;
        cout<<"size3:"<<size3<<endl;
        size1++;
        size2++;
        size3++;
		assert(sum == sum2);
	}

	return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <iostream>
#include "openacc.h"

using namespace std;


int main(){
	int arr[100000];
	int sum = 0 ;
	int sum2 = 0 ;
	int arr_size = 1;

    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 



	srand(time(NULL));

	while(arr_size<100000)
	{
		sum = 0 ; 
		sum2 = 0 ; 
		for(int i = 0 ; i < arr_size ; ++i)
		{
			arr[i] = rand()%100;
		}
	//	cout<<"enter input size"<<endl;
	//	cin>>arr_size;
		#pragma acc kernels copy(arr[0:arr_size])
		#pragma acc loop reduction(+:sum) independent
		for(int i = 0 ; i < arr_size ; ++i)
		{
			sum += arr[i];

		}
		for(int i = 0 ; i < arr_size ; ++i)
		{
			sum2 += arr[i];

		}
		cout<<"cpu result:"<<sum2<<endl;
		cout<<"gpu result:"<<sum<<endl;
        assert(sum2==sum);
		cout<<"array size:"<<arr_size<<endl;
		arr_size++;	
		assert(sum == sum2);
	}

	return 0;
}

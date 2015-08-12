/*
    This program searche a values in unordered vector and returns if find or not
    This program create a csv file with the time execution results for each function(CPU,GPU) in this format: size of vector,cpu time,gpu time.
    
    Author: Kezia Andrade
    Date: 04-07-2015
    version 1.0
    
    Run:
    folder_ipmacc/ipmacc folder_archive/search_in_vector.c
    ./a.out
*/

#include <openacc.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>

int SIZE;

float *a;
float c;

FILE *out;
FILE *result;

void init(int s) 
{
	int i;
	for (i = 0; i < s; ++i)
	{
        	a[i] = 2*i+7;
	}
}

void print_result(int s, int find) {
        int i;
        fprintf(result,"\nA:");
        for (i = 0; i < s; ++i)
        {
                fprintf(result,"%f ", a[i]);
        }
        fprintf(result,"\nC:%f",c);
        fprintf(result,"\nPosition:%d",find);
}

int search_GPU(int s)
{
	int i;
    	int find = -1;
	
	a = (float *) malloc(sizeof(float) * SIZE);
	c = (float)s-5;
	
	init(s);
	
	double start, finish, elapsed;
        start = (double) clock() / (CLOCKS_PER_SEC*1000);
	#pragma acc data copyin(a[0:s],c) copy(find)
        {
                #pragma acc kernels
                {
                        #pragma acc loop independent
                        {
				for (i = 0; i < s; ++i)
				{
        				if(a[i] == c)
        				{
            					find = i;
	    					i=s;
        				}
				}
			}
		}
	}
	
	acc_free(acc_deviceptr(a));

	finish = (double) clock() / (CLOCKS_PER_SEC*1000);
    elapsed = finish - start;
    fprintf(out,"%.6lf,",elapsed);
    	
	//print_result(s,find);
    free(a);
	
	return find;
}

int main(int argc, char *argv[]) {
	int i;
	
    if(argc != 2) {
		return 1;
	}
    
    SIZE = atoi(argv[1]);

	out = fopen("time_gpu.csv","w+");
	result = fopen("result_gpu.txt","w+");

	fprintf(out,"SIZE of vector,search GPU time,\n");
    int find;
	fprintf(out,"%d,",SIZE);
	find = search_GPU(SIZE);
	
	fclose(out);
	fclose(result);

	return 0;
}


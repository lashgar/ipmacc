/*
   This program performs string matching on the GPU with 
   dynamically allocated vector.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    ipmacc string-matching _gpu.c -o str
    ./str matrix-size
*/
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <string.h>
#include <openacc.h>
#include <time.h>

int SIZE;

char *frase;
char *palavra;

FILE *fil;
FILE *out;

/// initialize the two strings
int init(int size_1, int size_2)
{
	int i;
	for(i=0;i<size_1;i++)
	{
		frase[i] = 'a';
	}
	frase[i] = '\0';
	for(i=0;i<size_2;i++)
	{
		palavra[i] = 'a';
	}
	palavra[i] = '\0';
}

/// string matching algorithm GPU
/// s = size of longer string
/// p = size of less string
int string_matching_GPU(int size_1, int size_2)
{
    int i,diff,j,parallel_size, count = 0;
    diff  = size_1 - size_2;
    
    frase = (char *) malloc(sizeof(char) * (size_1+1));
    palavra = (char *) malloc(sizeof(char) * (size_2+1));
    
    init(size_1,size_2);
    float start, finish, elapsed;
    start = (float) clock() / (CLOCKS_PER_SEC * 1000);
    
    parallel_size = 10000;	
    int *vector;
    vector = (int *) malloc(sizeof(int) * parallel_size);
    for(i=0;i<parallel_size;i++)
    {
    	vector[i] = 0;
    }
    #pragma acc data copyin(frase[0:size_1],palavra[0:size_2]) copy(vector[0:parallel_size])
    {
    	#pragma acc kernels
    	{
    		#pragma acc loop independent
    		{
    			for(i=0;i<diff;i++)
    			{
    				int v;
    				v = 0;		
    				for(j=0;j<size_2;j++)
    				{
    					if(frase[(i+j)]!=palavra[j])
    					{
    						v = 1;
    					}
    				}
    				if(v==0)
    				{
    					vector[i%parallel_size]++;
    				}
    			}
    		}
    	}
    }
    acc_free(acc_deviceptr(frase));
    acc_free(acc_deviceptr(palavra));
    acc_free(acc_deviceptr(vector));
    
    for(i=0;i<parallel_size;i++)
    {
    	count += vector[i];
    }
    finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
    elapsed = finish - start;
    fprintf(fil,"%.6lf,",elapsed);
    
    free(frase);
	free(palavra);
	free(vector);
    
    return count;
}

int main(int argc, char *argv[]) 
{
    
    if(argc!=2) 
	{
		return 1;
	}
	
	SIZE = atoi(argv[1]);

    fil = fopen("time_gpu.csv","a");
    out = fopen("result_gpu.txt","a");

    fprintf(fil,"Size string,Size substring,String Matching GPU,\n");
    
    fprintf(fil,"%d,",SIZE);
    fprintf(fil,"%d,",(SIZE / 2));
    fprintf(out,"%d\n",string_matching_GPU(SIZE,(SIZE / 2)));
    fprintf(fil,"\n");

    fclose(fil);
    fclose(out);
    return 0;
}


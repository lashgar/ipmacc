/*
   This program performs matrix sum on the GPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    ipmacc mat-sum_gpu.c -o mat
    ./mat matrix-size
*/

#include <stdio.h>
#include <openacc.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int SIZE;

float *a;
float *b;
float *c;

FILE *fil;
FILE *out;

// Initialize matrices.
void init(int s) 
{
	int i, j;
	for (i = 0; i < s; ++i)
	{
		for (j = 0; j < s; ++j)
		{
			a[i * s + j] = (float)i + j;
			b[i * s + j] = (float)i + j;
			c[i * s + j] = 0.0f;
		}
	}
}

// Print the result matrix.
void print(int s) 
{
	int i, j;
	for (i = 0; i < s; ++i) 
	{
		for (j = 0; j < s; ++j)
		{
			fprintf(out,"%f ", c[i * s + j]);
		}
		fprintf(out,"\n");
	}
}

/// matrix sum algorithm GPU
/// s = size of matrix
void sum_GPU(int s) 
{
    a = (float *) malloc(sizeof(float) * SIZE * SIZE);
	b = (float *) malloc(sizeof(float) * SIZE * SIZE);
	c = (float *) malloc(sizeof(float) * SIZE * SIZE);

    init(s);    
    
	int i, j,q;
	q = s * s;
	float start, finish, elapsed;                       
	start = (float) clock() / (CLOCKS_PER_SEC * 1000); 
	#pragma acc data copyin(a[0:q],b[0:q]) copy(c[0:q])
	{
		#pragma acc kernels
		{
			#pragma acc loop independent
			{
				for (i = 0; i < s; ++i)
				{
					for (j = 0; j < s; ++j)
					{
						c[i * s + j] = a[i * s + j] + b[i * s + j];	
					}
				}
			}
		}
	}
	acc_free(a);
	acc_free(b);
	acc_free(c);
	
	finish = (float) clock() / (CLOCKS_PER_SEC * 1000);         
	elapsed = finish - start;
	fprintf(fil,"%.6lf,",elapsed);
	
	//print(s);
	free(a);
    free(b);
    free(c);	
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

	fprintf(fil,"SIZE,matrix sum gpu,\n");

	fprintf(fil,"%d,",SIZE);
	sum_GPU(SIZE);
	fprintf(fil,"\n");	  
		
	fclose(fil);
	fclose(out);
	return 0;
}


/*
   This program performs matrix multiplication on the GPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    ipmacc mat-mul_gpu.c -o mat
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
			a[i * s + j] = (float)i + j % 100;
			b[i * s + j] = (float)i + j % 100;
			c[i * s + j] = 0.0f;
		}
	}
}

// Print the result matrix.
void print(int s) {
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


/// matrix multiplication algorithm GPU
/// s = size of matrix
void mul_GPU(int s) 
{
	int i, j, k,l;
	l = s * s;
	
	a = (float *) malloc(sizeof(float) * SIZE * SIZE);
	b = (float *) malloc(sizeof(float) * SIZE * SIZE);
	c = (float *) malloc(sizeof(float) * SIZE * SIZE);
	init(SIZE);
	float sum = 0.0;
	float start, finish, elapsed;
	start = (float) clock() / (CLOCKS_PER_SEC * 1000);
	#pragma acc data copyin(a[0:l],b[0:l]) copy(c[0:l])
	{
		#pragma acc kernels
		{
			#pragma acc loop independent
			{
				for (i = 0; i < s; ++i) 
				{
					for (j = 0; j < s; ++j) 
					{
						sum = 0.0;
						for (k = 0; k < s; ++k) 
						{
							sum = sum + a[i * s + k] * b[k * s + j];
						}
						c[i * s + j] = sum;
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
	fprintf(fil,"%.10lf,",elapsed);
    //print(s);
    free(a);
    free(b);
    free(c);
}


int main(int argc, char *argv[]) {
	int i, points, var, limit;

	if(argc!=2) 
	{
		return 1;
	}
	
	SIZE = atoi(argv[1]);

	fil = fopen("time_gpu.csv","a");
	out = fopen("result_gpu.txt","a");
	fprintf(fil,"SIZE,matrix multiplication GPU,\n");

    printf("i: %d\n", SIZE);
	fprintf(fil,"%d,",SIZE);
	mul_GPU(SIZE);
	fprintf(fil,"\n");
	fclose(fil);
	fclose(out);
	return 0;
}


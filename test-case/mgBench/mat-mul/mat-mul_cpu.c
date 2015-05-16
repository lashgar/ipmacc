/*
   This program performs matrix multiplication on the CPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    gcc -O3 mat-mul_cpu.c -o mat
    ./mat matrix-size
*/

#include <stdio.h>
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

/// matrix multiplication algorithm CPU
/// s = size of matrix
void mul_CPU(int s)
{
    a = (float *) malloc(sizeof(float) * SIZE * SIZE);
	b = (float *) malloc(sizeof(float) * SIZE * SIZE);
	c = (float *) malloc(sizeof(float) * SIZE * SIZE);

    init(SIZE);

	int i,j,k;
	float sum = 0.0;
	float start, finish, elapsed;
	start = (float) clock() / (CLOCKS_PER_SEC * 1000);
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
	finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
	elapsed = finish - start;
	fprintf(fil,"%.10lf,",elapsed);
	
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

	fil = fopen("time_cpu.csv","w+");
	out = fopen("result_cpu.txt","w+");

	fprintf(fil,"SIZE,matrix multiplication CPU,\n");

	fprintf(fil,"%d,",SIZE);
	mul_CPU(SIZE);
	fprintf(fil,"\n");	  

	fclose(fil);
	fclose(out);
	return 0;
}


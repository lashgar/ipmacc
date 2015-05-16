/*
   This program performs cholesky decomposition on the CPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    gcc -O3 cholesky.c -o mat -lm
    ./cholesky matrix-size
*/

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

int SIZE;

float *a;
float *b;

FILE *fil;
FILE *out;

// Initialize matrices.
void init(int s) 
{
    int i, j,q;
    q = s * s;
    for (i = 0; i < s; ++i) 
    {
        for (j = 0; j < s; ++j) 
        {
            a[i * s + j] = (float)(q-(10*i)-(5*j));
            b[i * s + j] = 0.0f;
        }
    }
}

void print_matrix(int s)
{
	int i,j;
	for(i=0;i<s;i++)
	{
		for(j=0;j<s;j++)
		{
			fprintf(out,"%.0f ",b[i*s+j]);
		}
		fprintf(out,"\n");
	}
	fprintf(out,"\n");
}

/// Cholesky algorithm CPU
/// s = size of matrix
void cholesky_CPU(int s) 
{
    int i,j,k;
    
    a = (float *) malloc(sizeof(float) * s * s);
    b = (float *) malloc(sizeof(float) * s * s);
    init(s);
    
    float start, finish, elapsed;
    start = (float) clock() / (CLOCKS_PER_SEC * 1000);
	for(i = 0; i < s; i++)
    {
	      for(j = 0; j <= i; j++) 
	      {
	          float t;
	          t = 0.0f;
	          for (k = 0; k < j; k++)
	          {
		              t += b[i*s+k] * b[j*s+k];
	          }
	          if(i==j)
	          {
		              b[i*s+j] = sqrt((a[i*s+i]-t));
	          }
	          else
	          {
		              b[i*s+j] = (1.0/ b[j*s+j] * (a[i*s+j]-t));
	          }
	      }
    }
    finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
    elapsed = finish - start;
    fprintf(fil,"%.10f,",elapsed);
    
    //print_matrix(SIZE);
    
    free(a);
    free(b);
}

int main(int argc, char *argv[]) 
{
    if(argc!=2) 
	{
		return 1;
	}
	
	SIZE = atoi(argv[1]);

    fil = fopen("time_cpu.csv","a");
    out = fopen("result_cpu.txt","a");

    fprintf(fil,"SIZE,cholesky CPU,\n");
        
    fprintf(fil,"%d,",SIZE);
    cholesky_CPU(SIZE); 
	
	fprintf(fil,"\n");
	
    fclose(fil);
    fclose(out);
    return 0;
}


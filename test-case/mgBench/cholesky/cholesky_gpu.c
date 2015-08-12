/*
   This program performs cholesky decomposition on the GPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendon?a 
    Date: 04-01-2015
    version 2.0
    
    Run:
    ipmacc cholesky_gpu.c -o cholesky
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

/// Cholesky algorithm GPU
/// s = size of matrix
void cholesky_GPU(int s) 
{
    int i,j,k,l;
    
	l = s*s;
    a = (float*) malloc(SIZE * SIZE * sizeof(float));
    b = (float*) malloc(SIZE * SIZE * sizeof(float));
    init(SIZE);
    
    float start, finish, elapsed;
    start = (float) clock() / (CLOCKS_PER_SEC * 1000);
    #pragma acc data copyin(a[0:l]) copy(b[0:l])
    {
        #pragma acc kernels
        {
            #pragma acc loop independent
            {
                for(i = 0; i < s; i++)
                {
                    for(j = 0; j <= i; j++) 
                    {
                        float t;
                        t = 0.0f;
                        for (k = 0; k < j; k++)
                        {
                            if(b[i*s+k]!=0.0f
                            &&b[j*s+k]!=0.0f)
                            {
                                t += b[i*s+k] * b[j*s+k];
                            }
                            else
                            {
                                k--;
                            }
                        }
                        if(i==j)
                        {
                            b[i*s+j] = sqrt((a[i*s+i]-t));
                        }
                        else
                        {
                            if(b[j*s+j]!=0.0f)
                            {
                                b[i*s+j] = (1.0/ b[j*s+j] * (a[i*s+j]-t));
                            }
                            else
                            {
                                j--;
                            }
                        }
                    }
                }     
            }
        }
    }
    acc_free(acc_deviceptr(a));
	acc_free(acc_deviceptr(b));
    
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
    
    fil = fopen("time_gpu.csv","a");
    out = fopen("result_gpu.txt","a");

    fprintf(fil,"SIZE,cholesky GPU,\n");
  
    fprintf(fil,"%d,",SIZE);
    cholesky_GPU(SIZE); 
    fprintf(fil,"\n");

    fclose(fil);
    fclose(out);

	return 0;
}


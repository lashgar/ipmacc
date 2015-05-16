/*
    This program makes the decomposition of matrices.
    It receives an input array and returns two triangular matrices in the same array b.
    This program create a csv file with the time execution results for each function(CPU,GPU) in this format: size of matrix, cpu time, gpu time.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 1.0
    
    Run:
    folder_ipmacc/ipmacc folder_archive/LU_decomposition.c
    ./a.out
*/

#include <stdio.h>
#include <openacc.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <limits.h>

#define SIZE 510

float a[SIZE * SIZE];
float b[SIZE * SIZE];

FILE *fil;
FILE *out;

// Initialize matrices.
void init(int s) {
    int i, j,q;
    q = s * s;
    for (i = 0; i < s; ++i) 
    {
        for (j = 0; j < s; ++j)
        {
            a[i * s + j] = (float)(q-(10*i + 5*j));
            b[i * s + j] = 0.0f;
        }
    }
}

/// Crout algorithm GPU
/// s = size of matrix
void Crout_GPU(int s){
	int k,j,i;
	float sum;
	double start, finish, elapsed;
	start = (double) clock() / CLOCKS_PER_SEC;

    #pragma acc data pcopyin(a[0:s]) pcopy(b[0:s])
    {
        #pragma acc kernels pcopyin(a) pcopy(b)
        {
            #pragma acc loop independent
            {
                for(k=0;k<s;++k)
                {
                    for(j=k;j<s;++j)
                    {
                        sum=0.0;
                        for(i=0;i<k;++i)
                        {
                            sum+=b[j*s+i]*b[i*s+k];
                        }
                        b[j*s+k]=(a[j*s+k]-sum); // not dividing by diagonals
                    }
                    for(i=k+1;i<s;++i)
                    {
                        sum=0.0;
                        for(j=0;j<k;++j)
                        {
                            sum+=b[k*s+j]*b[i*s+i];
                        }
                        b[k*s+i]=(a[k*s+i]-sum)/b[k*s+k];
                    }
                }
            }
        }
    }

	finish = (double) clock() / CLOCKS_PER_SEC;
	elapsed = finish - start;
	fprintf(fil,"%.6lf;",elapsed);
}

/// print matrix in the standard output
/// s = size of matrix
void print_matrix(int s)
{
	int i,j;
	for(i=0;i<s;i++)
	{
		for(j=0;j<s;j++)
		{
			if(b[i*s+j]==INT_MAX)
			{
				continue;
			}
			fprintf(out,"%.6f ", b[i*s+j]);
		}
		fprintf(out,"\n");
	}
}

int main(int argc, char *argv[]) 
{
    int i;
    int points, var;
    points = atoi(argv[1]);
    var = SIZE/points; 
    
    fil = fopen("time_gpu.csv","w+");
    out = fopen("result_gpu.txt","w+");
    fprintf(fil,"SIZE,LU decomposition GPU,\n");
    for(i=2;i<SIZE;i+=var)
    {
        init(i);
    	fprintf(fil,"%d,",i);
        Crout_GPU(i);
        fprintf(fil,"\n");	  
    }
    fclose(fil);
    fclose(out);
    return 0;
}





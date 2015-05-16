/*
   
    This program calculates the distance between the k neighbors in a Cartesian map.
    It generates a matrix with the distance between the neighbors.
    This program create a csv file with the time execution results for each function(CPU,GPU) in this format: size of matrix, cpu time, gpu time.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 1.0
    
    Run:
    folder_ipmacc/ipmacc folder_archive/k-nearest.c
    ./a.out
*/

#include <stdio.h>
#include <stdlib.h>
#include <openacc.h>
#include <math.h>
#include <limits.h>
#include <time.h>

#define SIZE 1510

int matrix[SIZE * SIZE];
int matrix_dist[SIZE * SIZE];

FILE *fil;
FILE *out;

/// initialize the cartesian map
void init(int s)
{
    int i,j,r,m;
    for(i=0;i<s;i++)
    {
        for(j=0;j<s;j++)
        {
            matrix[i*s+j] = 99999999;
            matrix_dist[i*s+j] = 99999999;
        }
    }
    for(i=0;i<s;i++)
    {
        r = (i*97)%s;
        for(j=0;j<r;j++)
        {
            m = (((j*1021)*71 % (s * s))+1);
            matrix[i*s+j] = m;
        }
    }
}


/// Knearest algorithm GPU
/// s = size of cartesian map
void Knearest_GPU(int s)
{
    int i,j,k;
    for(i=0;i<s;i++)
    {
        for(j=0;j<s;j++)
        {
            if(matrix[i*s+j]!=99999999)
            {
                matrix_dist[i*s+j] = matrix[i*s+j];
            }
        }
        matrix_dist[i*s+i] = 0;
    }
    /// opportunity of parallelism here
    float start, finish, elapsed;
    start = (float) clock() / (CLOCKS_PER_SEC * 1000);
    #pragma acc data copy(matrix_dist[0:s])
    {
        for(k=0;k<s;k++)
        {
            for(i=0;i<s;i++)
            {
                #pragma acc kernels
                {
                    #pragma acc loop independent
                    {
                        for(j=0;j<s;j++)
                        {
                            if(matrix_dist[i*s+k]!=99999999 &&
                            matrix_dist[k*s+j]!=99999999 &&
                            matrix_dist[i*s+j]>matrix_dist[i*s+k]+matrix_dist[k*s+j])
                            { 
                                  matrix_dist[i*s+j] = matrix_dist[i*s+k] + matrix_dist[k*s+j];
                            }
                        }
                    }
                }
            }
        }
    }
    acc_free(matrix_dist);
    finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
    elapsed = finish - start;
    fprintf(fil,"%.6lf,",elapsed);
}

/// print the distances calculated
void print_distances(int s)
{
	int i,j;
	for(i=0;i<s;i++)
	{
		for(j=0;j<s;j++)
		{
			if(matrix_dist[i*s+j]==99999999){continue;}
			fprintf(out,"%d ", matrix_dist[i*s+j]);
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

    fprintf(fil,"SIZE,K-nearest GPU\n");
    for(i=(var-1);i<SIZE;i+=var)
    {
        init(i);
        fprintf(fil,"%d,",i);
        Knearest_GPU(i);
        //print_distances(i);
	    fprintf(fil,"\n");
    }
    
    fclose(fil);
    fclose(out);
    return 0;
}


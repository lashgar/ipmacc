/*
    This program checks the collinearity of points.
    It receives an input a vector with points and returns the mathematical functions that pass these points. It have a list to store answers.
    This program create a csv file with the time execution results for each function(CPU,GPU) in this format: size of vector, cpu with list time, gpu with list time.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-05-2015
    version 2.0
    
    Run:
    folder_ipmacc/ipmacc folder_archive/colinear_v2.c
    ./a.out
*/
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <limits.h>
#include <time.h>
#include <string.h>

typedef struct point
{
	int x;
	int y;
} point;

int SIZE;

point *points;

FILE *fil;
FILE *out;

void generate_points(int size)
{
	int i;
     for(i=0;i<size;i++)
	{
		points[i].x = (i*777)%11;
		points[i].y = (i*777)%13;
	}
}

/// colinear list algorithm CPU
/// N = size of vector
int colinear_list_points_CPU(int N)
{
	
	int i,j,k,val;
	val = 0;
	points = (point *) malloc(sizeof(points)*N);
	generate_points(N);
	
	float start, finish, elapsed;
	start = (float) clock() / (CLOCKS_PER_SEC * 1000);
	for(i = 0; i < N; i++)
	{
		for(j = 0; j < N; j++)
		{
			for(k = 0; k < N; k++)
			{
				/// to understand if is colinear points
				int slope_coefficient,linear_coefficient;
				int ret;
				ret = 0;
				slope_coefficient = points[j].y - points[i].y;
				
				if((points[j].x - points[i].x)!=0)
				{
					slope_coefficient = slope_coefficient / (points[j].x - points[i].x);
					linear_coefficient = points[i].y - (points[i].x * slope_coefficient);
					
					if(slope_coefficient!=0
					&&linear_coefficient!=0
					&&points[k].y == (points[k].x * slope_coefficient) + linear_coefficient)
					{

						ret = 1;
					}
				}
				/// to list add
				if(ret==1)
				{
					val = 1;
				}
			}
		}
	}
	finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
	elapsed = finish - start;
	fprintf(fil,"%.10lf,",elapsed);
    free(points);
    return val;
}

int main(int argc, char *argv[])
{
	if(argc!=2) 
	{
		return 1;
	}
	SIZE = atoi(argv[1]);
	
	fil = fopen("time_cpu.csv","a+");
	out = fopen("result_cpu.txt","a+");
    
  	fprintf(fil,"SIZE,collinear list CPU,\n");
	fprintf(fil,"%d,",SIZE);
	fprintf(out,"%d\n",colinear_list_points_CPU(SIZE));
	fprintf(fil,"\n");

	fclose(fil);
	fclose(out);
	return 0;
}

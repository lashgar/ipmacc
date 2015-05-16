/*
   This program performs string matching on the CPU with 
   dynamically allocated vector.
    
    Author: Gleison Souza Diniz Mendonça 
    Date: 04-01-2015
    version 2.0
    
    Run:
    gcc -O3 string-matching _cpu.c -o str
    ./str matrix-size
*/


#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <limits.h>
#include <string.h>
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

/// string matching algorithm CPU
/// s = size of longer string
/// p = size of less string
int string_matching_CPU(int size_1, int size_2)
{
    frase = (char *) malloc(sizeof(char) * (size_1+1));
    palavra = (char *) malloc(sizeof(char) * (size_2+1));

    init(size_1,size_2);
	int i,j,diff, count;
	diff = size_1 - size_2;
	count = 0;
	float start, finish, elapsed;
	start = (float) clock() / (CLOCKS_PER_SEC * 1000);
	
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
			count++;
		}	
	}
	
	finish = (float) clock() / (CLOCKS_PER_SEC * 1000);
	elapsed = finish - start;
	fprintf(fil,"%.6lf,",elapsed);
	
	free(frase);
	free(palavra);
	return count;
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

    fprintf(fil,"Size string,Size substring,String Matching CPU,\n");
    
    fprintf(fil,"%d,",SIZE);
    fprintf(fil,"%d,",(SIZE / 2));
    fprintf(out,"%d\n",string_matching_CPU(SIZE,(SIZE / 2)));
    fprintf(fil,"\n");

    fclose(fil);
    fclose(out);
    return 0;
}


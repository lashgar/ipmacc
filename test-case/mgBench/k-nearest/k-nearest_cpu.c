/*
   This program performs K nearest neighbors on the CPU with 
   dynamically allocated matrices.
    
    Author: Gleison Souza Diniz Mendon?a 
    Date: 04-01-2015
    version 2.0
    
    Run:
    gcc -O3 k-nearest_cpu.c -o k-nearest
    ./k-nearest matrix-size
*/
#include <stdlib.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

typedef struct point
{
    int x;
    int y;
}point;

typedef struct sel_points
{
    int position;
    float value;
}sel_points;

int SIZE;
#define default_v 100000.00

point *pivots;
point *the_points;
sel_points *selected;

FILE *fil;
FILE *out;

void init(int s,int t)
{
    int i,j;
    for(i=0;i<t;i++)
    {
        pivots[i].x = i*3;
        pivots[i].y = i*2;
    }
    for(i=0;i<s;i++)
    {
        the_points[i].x = i*3;
        the_points[i].y = i*2;
        
        for(j=0;j<s;j++)
        {
            selected[i*s+j].position = 0;
            selected[i*s+j].value = default_v;
        }
    }
}

void order_points(int s,int t)
{
    int i;
    for(i=0;i<t;i++)
    {
    
        /// for each line in matrix
        /// order values
        int j;
        for(j=0;j<s;j++)
        {
            int m;
            for(m=j+1;m<s;m++)
            {
                if(selected[i*s+j].value>selected[i*s+m].value)
                {
                    sel_points aux;
                    aux = selected[i*s+j];
                    selected[i*s+j] = selected[i*s+m];
                    selected[i*s+m] = aux;
                }
            } 
           
        }
    }
}

void print(int s,int k, int t)
{
    int i;
    for(i=0;i<t;i++)
    {
        int j;
        for(j=0;j<=k;j++)
        {
            int pos_sel;
            pos_sel = selected[i*s+j].position;
            fprintf(out,"pivot position %d (%d ; %d), point nearest %d (%d ; %d), distance %.0f\n"
            ,i,pivots[i].x,pivots[i].y,pos_sel,the_points[pos_sel].x,the_points[pos_sel].y,selected[i*s+j].value);
        }
        fprintf(out,"\n");
    }
    fprintf(out,"\n");
}

void k_nearest_cpu(int s,int t)
{
    pivots = (point *) malloc(sizeof(point) * s);
    the_points = (point *) malloc(sizeof(point) * s);
    selected = (sel_points *)malloc(sizeof(sel_points) * s * s);
    
    float start, finish, elapsed;
    start = (float) clock() / (CLOCKS_PER_SEC*1000);
    
    init(s,t);
    
    int i,j;
    for(i=0;i<t;i++)
    {
        for(j=0;j<s;j++)
        {
            float distance,x,y;
            x = pivots[i].x - the_points[j].x;
            y = pivots[i].y - the_points[j].y;
            x = x * x;
            y = y * y;
            
            distance = x + y;
            distance = sqrt(distance);
            
            selected[i*s+j].value = distance;
            selected[i*s+j].position = j;
        }
    }
    
    order_points(s,t);

    finish = (float) clock() / (CLOCKS_PER_SEC*1000);
    elapsed = finish - start;
    fprintf(fil,"%.9lf,",elapsed);
     
    //print(s,t,t);
     
    free(pivots);
    free(the_points);
    free(selected);
}

int main(int argc, char *argv[])
{
    fil = fopen("time_cpu.csv","a");
    out = fopen("result_cpu.txt","a");

    if(argc!=2)
	{
	    printf("Error, you need to run in this format:\n./executable_name size\n");
	}
	SIZE = atoi(argv[1]);
    
    fprintf(fil,"SIZE, K, K-nearest cpu time,\n");
    fprintf(fil,"%d,%d,",SIZE,(SIZE / 2));
    
    k_nearest_cpu(SIZE,(SIZE / 2));
   
    fprintf(fil,"\n");

    fclose(fil);
    fclose(out);
    return 0;
}


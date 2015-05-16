#include <stdlib.h>
#include <stdio.h>
#include <openacc.h>
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

#define SIZE 510
#define default_v 100000.00

point vector[SIZE];
sel_points selected[SIZE * SIZE];

FILE *fil;
FILE *out;

void init(int s)
{
    int i,j;
    for(i=0;i<s;i++)
    {
        vector[i].x = i;
        vector[i].y = i*2;
    }
    for(i=0;i<s;i++)
    {
        for(j=0;j<s;j++)
        {
            selected[i*s+j].position = 0;
            selected[i*s+j].value = default_v;
        }
    }
}

void k_nearest_cpu(int s)
{
    int i,j,m,q;
    q = s*s;
    #pragma acc data copyin(vector[0:s]) copy(selected[0:q])
    {
        #pragma acc kernels
        {
            #pragma acc loop independent
            {
                for(i=0;i<s;i++)
                {
                    for(j=i+1;j<s;j++)
                    {
                        float distance,x,y;
                        x = vector[i].x - vector[j].x;
                        y = vector[i].y - vector[j].y;
                        x = x * x;
                        y = y * y;
                        
                        distance = x + y;
                        distance = sqrt(distance);
                        
                        selected[i*s+j].value = distance;
                        selected[i*s+j].position = j;
                        
                        selected[j*s+i].value = distance;
                        selected[j*s+i].position = i;
                    }
                }
            }
        }
        
        
        #pragma acc kernels
        {
            #pragma acc loop independent
            {
                for(i=0;i<s;i++)
                {
                
                    /// for each line in matrix
                    /// order values
                    for(j=0;j<s;j++)
                    {
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
        }
        
    }
    acc_free(vector);
    acc_free(selected);
}

void print(int s, int k)
{
    int i;
    for(i=0;i<s;i++)
    {
        int j;
        for(j=0;j<=k;j++)
        {
            int pos_sel;
            pos_sel = selected[i*s+j].position;
            fprintf(out,"point position %d , point nearest %d (%d ; %d), distance %.2f\n"
            ,i,pos_sel,vector[pos_sel].x,vector[pos_sel].y,selected[i*s+j].value);
        }
        fprintf(out,"\n");
    }
    fprintf(out,"\n");
}

int main(int argc, char *argv[])
{
    fil = fopen("time_gpu.csv","w+");
    out = fopen("result_gpu.txt","w+");
    
    int i,j,points,var;
    if(argc<2)
    {
      printf("Number of points is unknown.\n");
      return;
    }
    points = atoi(argv[1]);
    var = SIZE/points;
    
    
    fprintf(fil,"SIZE, K, nearest gpu time,\n");
    for(i=(var-1);i<SIZE;i+=var)
    {
        j = i/2;
        fprintf(fil,"%d,%d,",i,j);
        init(i);
        
        /// monitored time
        /// start of algorithm
        float start, finish, elapsed;
	      start = (float) clock() / (CLOCKS_PER_SEC*1000);
       
        k_nearest_cpu(i);
        //order_points(i);
        
        finish = (float) clock() / (CLOCKS_PER_SEC*1000);
	      elapsed = finish - start;
	      fprintf(fil,"%.9lf,",elapsed);
	      /// end of algorithm
	      
        print(i,j);
        fprintf(fil,"\n");
    }

    fclose(fil);
    fclose(out);
    return 0;
}


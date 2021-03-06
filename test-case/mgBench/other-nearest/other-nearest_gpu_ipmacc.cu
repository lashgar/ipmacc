#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <cuda.h>

#include <stdlib.h>
#include <stdio.h>
#include <openacc.h>
#include <math.h>
#include <time.h>

typedef struct point
{
  int x;
  int y;
} point;

typedef struct sel_points
{
  int position;
  float value;
} sel_points;

#define SIZE 510
#define default_v 100000.00

point vector[SIZE];
sel_points selected[SIZE * SIZE];

FILE *fil;
FILE *out;

void
init (int s)
{
  int i, j;
  for (i = 0; i < s; i++)
    {
      vector[i].x = i;
      vector[i].y = i * 2;
    }
  for (i = 0; i < s; i++)
    {
      for (j = 0; j < s; j++)
	{
	  selected[i * s + j].position = 0;
	  selected[i * s + j].value = default_v;
	}
    }
}

__global__ void __generated_kernel_region_0 (int s, point * vector,
					     sel_points * selected);

__global__ void __generated_kernel_region_1 (sel_points * selected, int s);

void
k_nearest_cpu (int s)
{
  int i, j, m, q;
  q = s * s;


  ipmacc_prompt ((char *) "IPMACC: memory allocation selected\n");
  acc_create ((void *) selected, SIZE * SIZE * sizeof (sel_points));
  ipmacc_prompt ((char *) "IPMACC: memory allocation vector\n");
  acc_create ((void *) vector, SIZE * sizeof (point));
  ipmacc_prompt ((char *) "IPMACC: memory copyin selected\n");
  acc_copyin ((void *) selected, SIZE * SIZE * sizeof (sel_points));
  ipmacc_prompt ((char *) "IPMACC: memory copyin vector\n");
  acc_copyin ((void *) vector, SIZE * sizeof (point));


  {


    {



/* kernel call statement [0, -1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		(((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_0 <<< (((abs (((s)) - 0)) / (1))) / 256 + 1,
	256 >>> (s, (point *) acc_deviceptr ((void *) vector),
		 (sel_points *) acc_deviceptr ((void *) selected));
/* kernel call statement*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();








/* kernel call statement [0, -1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 1 > gridDim: %d\tblockDim: %d\n",
		(((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_1 <<< (((abs (((s)) - 0)) / (1))) / 256 + 1,
	256 >>> ((sel_points *) acc_deviceptr ((void *) selected), s);
/* kernel call statement*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();



    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout selected\n");
  acc_copyout_and_keep ((void *) selected, SIZE * SIZE * sizeof (sel_points));



  acc_free (vector);
  acc_free (selected);
}

void
print (int s, int k)
{
  int i;
  for (i = 0; i < s; i++)
    {
      int j;
      for (j = 0; j <= k; j++)
	{
	  int pos_sel;
	  pos_sel = selected[i * s + j].position;
	  fprintf (out,
		   "point position %d , point nearest %d (%d ; %d), distance %.2f\n",
		   i, pos_sel, vector[pos_sel].x, vector[pos_sel].y,
		   selected[i * s + j].value);
	}
      fprintf (out, "\n");
    }
  fprintf (out, "\n");
}

int
main (int argc, char *argv[])
{
  fil = fopen ("time_gpu.csv", "w+");
  out = fopen ("result_gpu.txt", "w+");

  int i, j, points, var;
  if (argc < 2)
    {
      printf ("Number of points is unknown.\n");
      return;
    }
  points = atoi (argv[1]);
  var = SIZE / points;


  fprintf (fil, "SIZE, K, nearest gpu time,\n");
  for (i = (var - 1); i < SIZE; i += var)
    {
      j = i / 2;
      fprintf (fil, "%d,%d,", i, j);
      init (i);



      float start, finish, elapsed;
      start = (float) clock () / (CLOCKS_PER_SEC * 1000);

      k_nearest_cpu (i);


      finish = (float) clock () / (CLOCKS_PER_SEC * 1000);
      elapsed = finish - start;
      fprintf (fil, "%.9lf,", elapsed);


      print (i, j);
      fprintf (fil, "\n");
    }

  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (int s, point * vector, sel_points * selected)
{
  int __kernel_getuid = threadIdx.x + blockIdx.x * blockDim.x;
  int i;
  int j;
  {
    {


      {
	{


	  {
	    i = 0 + (__kernel_getuid);
	    if (i < s)
	      {
		for (j = i + 1; j < s; j++)
		  {
		    float distance, x, y;
		    x = vector[i].x - vector[j].x;
		    y = vector[i].y - vector[j].y;
		    x = x * x;
		    y = y * y;

		    distance = x + y;
		    distance = sqrt (distance);

		    selected[i * s + j].value = distance;
		    selected[i * s + j].position = j;

		    selected[j * s + i].value = distance;
		    selected[j * s + i].position = i;
		  }
	      }

	  }
	}
      }
    }
  }
}

__global__ void
__generated_kernel_region_1 (sel_points * selected, int s)
{
  int __kernel_getuid = threadIdx.x + blockIdx.x * blockDim.x;
  int i;
  int j;
  int m;
  {
    {


      {
	{


	  {
	    i = 0 + (__kernel_getuid);
	    if (i < s)
	      {
		for (j = 0; j < s; j++)
		  {
		    for (m = j + 1; m < s; m++)
		      {
			if (selected[i * s + j].value >
			    selected[i * s + m].value)
			  {
			    sel_points aux;
			    aux = selected[i * s + j];
			    selected[i * s + j] = selected[i * s + m];
			    selected[i * s + m] = aux;
			  }
		      }
		  }
	      }

	  }
	}
      }
    }
  }
}

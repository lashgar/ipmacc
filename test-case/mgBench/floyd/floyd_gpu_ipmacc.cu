#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <cuda.h>



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


void
init (int s)
{
  int i, j, r, m;
  for (i = 0; i < s; i++)
    {
      for (j = 0; j < s; j++)
	{
	  matrix[i * s + j] = 99999999;
	  matrix_dist[i * s + j] = 99999999;
	}
    }
  for (i = 0; i < s; i++)
    {
      r = (i * 97) % s;
      for (j = 0; j < r; j++)
	{
	  m = (((j * 1021) * 71 % (s * s)) + 1);
	  matrix[i * s + j] = m;
	}
    }
}



__global__ void __generated_kernel_region_0 (int i, int k, int s,
					     int *matrix_dist);

void
Knearest_GPU (int s)
{
  int i, j, k;
  for (i = 0; i < s; i++)
    {
      for (j = 0; j < s; j++)
	{
	  if (matrix[i * s + j] != 99999999)
	    {
	      matrix_dist[i * s + j] = matrix[i * s + j];
	    }
	}
      matrix_dist[i * s + i] = 0;
    }

  float start, finish, elapsed;
  start = (float) clock () / (CLOCKS_PER_SEC * 1000);


  ipmacc_prompt ((char *) "IPMACC: memory allocation matrix_dist\n");
  acc_create ((void *) matrix_dist, SIZE * SIZE * sizeof (int));
  ipmacc_prompt ((char *) "IPMACC: memory copyin matrix_dist\n");
  acc_copyin ((void *) matrix_dist, SIZE * SIZE * sizeof (int));


  {


    {

      for (k = 0; k < s; k++)
	{

	  for (i = 0; i < s; i++)
	    {



/* kernel call statement [0, -1]*/
	      if (getenv ("IPMACC_VERBOSE"))
		printf
		  ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		   (((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
	      __generated_kernel_region_0 <<< (((abs (((s)) - 0)) / (1))) /
		256 + 1, 256 >>> (i, k, s,
				  (int *) acc_deviceptr ((void *)
							 matrix_dist));
/* kernel call statement*/
	      if (getenv ("IPMACC_VERBOSE"))
		printf ("IPMACC: Synchronizing the region with host\n");
	      cudaDeviceSynchronize ();



	    }


	}


    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout matrix_dist\n");
  acc_copyout_and_keep ((void *) matrix_dist, SIZE * SIZE * sizeof (int));



  acc_free (matrix_dist);
  finish = (float) clock () / (CLOCKS_PER_SEC * 1000);
  elapsed = finish - start;
  fprintf (fil, "%.6lf,", elapsed);
}


void
print_distances (int s)
{
  int i, j;
  for (i = 0; i < s; i++)
    {
      for (j = 0; j < s; j++)
	{
	  if (matrix_dist[i * s + j] == 99999999)
	    {
	      continue;
	    }
	  fprintf (out, "%d ", matrix_dist[i * s + j]);
	}
      fprintf (out, "\n");
    }
}

int
main (int argc, char *argv[])
{
  int i;
  int points, var;
  points = atoi (argv[1]);
  var = SIZE / points;

  fil = fopen ("time_gpu.csv", "w+");
  out = fopen ("result_gpu.txt", "w+");

  fprintf (fil, "SIZE,K-nearest GPU\n");
  for (i = (var - 1); i < SIZE; i += var)
    {
      init (i);
      fprintf (fil, "%d,", i);
      Knearest_GPU (i);
      print_distances (i);
      fprintf (fil, "\n");
    }

  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (int i, int k, int s, int *matrix_dist)
{
  int __kernel_getuid = threadIdx.x + blockIdx.x * blockDim.x;
  int j;
  {
    {


      {
	{


	  {
	    j = 0 + (__kernel_getuid);
	    if (j < s)
	      {
		if (matrix_dist[i * s + k] != 99999999 &&
		    matrix_dist[k * s + j] != 99999999 &&
		    matrix_dist[i * s + j] >
		    matrix_dist[i * s + k] + matrix_dist[k * s + j])
		  {
		    matrix_dist[i * s + j] =
		      matrix_dist[i * s + k] + matrix_dist[k * s + j];
		  }
	      }

	  }
	}
      }
    }
  }
}

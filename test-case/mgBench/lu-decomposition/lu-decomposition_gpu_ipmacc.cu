#include <stdlib.h>
#include <stdio.h>
#include <assert.h>
#include <openacc.h>
#define IPMACC_MAX1(A)   (A)
#define IPMACC_MAX2(A,B) (A>B?A:B)
#define IPMACC_MAX3(A,B,C) (A>B?(A>C?A:(B>C?B:C)):(B>C?C:B))
#include <cuda.h>



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


void
init (int s)
{
  int i, j, q;
  q = SIZE * SIZE;
  for (i = 0; i < s; ++i)
    {
      for (j = 0; j < s; ++j)
	{
	  a[i * s + j] = (float) ((s * s) - (i + j));
	  b[i * s + j] = 0.0f;
	}
    }
}



__global__ void __generated_kernel_region_0 (float *a, float *b, int s,
					     float sum);

void
Crout_GPU (int s)
{
  int k, j, i;
  float sum;
  double start, finish, elapsed;
  start = (double) clock () / CLOCKS_PER_SEC;



  ipmacc_prompt ((char *) "IPMACC: memory allocation b\n");
  acc_present_or_create ((void *) b, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory allocation a\n");
  acc_present_or_create ((void *) a, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin b\n");
  acc_pcopyin ((void *) b, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin a\n");
  acc_pcopyin ((void *) a, SIZE * SIZE * sizeof (float));


  {


    {


      ipmacc_prompt ((char *) "IPMACC: memory allocation b\n");
      acc_present_or_create ((void *) b, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory allocation a\n");
      acc_present_or_create ((void *) a, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory copyin b\n");
      acc_pcopyin ((void *) b, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory copyin a\n");
      acc_pcopyin ((void *) a, SIZE * SIZE * sizeof (float));

/* kernel call statement [0, 1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		(((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_0 <<< (((abs (((s)) - 0)) / (1))) / 256 + 1,
	256 >>> ((float *) acc_deviceptr ((void *) a),
		 (float *) acc_deviceptr ((void *) b), s, sum);
/* kernel call statement*/
      ipmacc_prompt ((char *) "IPMACC: memory copyout b\n");
      acc_copyout_and_keep ((void *) b, SIZE * SIZE * sizeof (float));
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();



    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout b\n");
  acc_copyout_and_keep ((void *) b, SIZE * SIZE * sizeof (float));




  finish = (double) clock () / CLOCKS_PER_SEC;
  elapsed = finish - start;
  fprintf (fil, "%.6lf;", elapsed);
}



void
print_matrix (int s)
{
  int i, j;
  for (i = 0; i < s; i++)
    {
      for (j = 0; j < s; j++)
	{
	  if (b[i * s + j] == INT_MAX)
	    {
	      continue;
	    }
	  fprintf (out, "%.6f ", b[i * s + j]);
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
  fprintf (fil, "SIZE,LU decomposition GPU,\n");
  for (i = 2; i < SIZE; i += var)
    {
      init (i);
      fprintf (fil, "%d,", i);
      Crout_GPU (i);
      fprintf (fil, "\n");
    }
  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (float *a, float *b, int s, float sum)
{
  int __kernel_getuid = threadIdx.x + blockIdx.x * blockDim.x;
  int i;
  int k;
  int j;
  {
    {


      {
	{


	  {
	    k = 0 + (__kernel_getuid);
	    if (k < s)
	      {
		for (j = k; j < s; ++j)
		  {
		    sum = 0.0;
		    for (i = 0; i < k; ++i)
		      {
			sum += b[j * s + i] * b[i * s + k];
		      }
		    b[j * s + k] = (a[j * s + k] - sum);
		  }

		for (i = k + 1; i < s; ++i)
		  {
		    sum = 0.0;
		    for (j = 0; j < k; ++j)
		      {
			sum += b[k * s + j] * b[i * s + i];
		      }
		    b[k * s + i] = (a[k * s + i] - sum) / b[k * s + k];
		  }
	      }

	  }
	}
      }
    }
  }
}

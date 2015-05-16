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
#define SIZE 1210

float a[SIZE * SIZE];
float b[SIZE * SIZE];
float c[SIZE * SIZE];

FILE *fil;
FILE *out;


void
init (int s)
{
  int i, j;
  for (i = 0; i < s; ++i)
    {
      for (j = 0; j < s; ++j)
	{
	  a[i * s + j] = (float) i + j;
	  b[i * s + j] = (float) i - j;
	  c[i * s + j] = 0.0f;
	}
    }
}



__global__ void __generated_kernel_region_0 (float *a, float *c, float *b,
					     int s);

void
sum_GPU (int s)
{
  int i, j;
  float start, finish, elapsed;
  start = (float) clock () / (CLOCKS_PER_SEC * 1000);


  ipmacc_prompt ((char *) "IPMACC: memory allocation c\n");
  acc_create ((void *) c, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory allocation a\n");
  acc_create ((void *) a, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory allocation b\n");
  acc_create ((void *) b, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin c\n");
  acc_copyin ((void *) c, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin a\n");
  acc_copyin ((void *) a, SIZE * SIZE * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin b\n");
  acc_copyin ((void *) b, SIZE * SIZE * sizeof (float));


  {


    {


      ipmacc_prompt ((char *) "IPMACC: memory allocation c\n");
      acc_create ((void *) c, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory allocation a\n");
      acc_create ((void *) a, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory allocation b\n");
      acc_create ((void *) b, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory copyin c\n");
      acc_copyin ((void *) c, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory copyin a\n");
      acc_copyin ((void *) a, SIZE * SIZE * sizeof (float));
      ipmacc_prompt ((char *) "IPMACC: memory copyin b\n");
      acc_copyin ((void *) b, SIZE * SIZE * sizeof (float));

/* kernel call statement [0, 1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		(((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_0 <<< (((abs (((s)) - 0)) / (1))) / 256 + 1,
	256 >>> ((float *) acc_deviceptr ((void *) a),
		 (float *) acc_deviceptr ((void *) c),
		 (float *) acc_deviceptr ((void *) b), s);
/* kernel call statement*/
      ipmacc_prompt ((char *) "IPMACC: memory copyout c\n");
      acc_copyout_and_keep ((void *) c, SIZE * SIZE * sizeof (float));
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();



    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout c\n");
  acc_copyout_and_keep ((void *) c, SIZE * SIZE * sizeof (float));



  acc_free (a);
  acc_free (b);
  acc_free (c);
  finish = (float) clock () / (CLOCKS_PER_SEC * 1000);
  elapsed = finish - start;
  fprintf (fil, "%.6lf,", elapsed);
}


void
print ()
{
  int i, j;
  for (i = 0; i < SIZE; ++i)
    {
      for (j = 0; j < SIZE; ++j)
	{
	  fprintf (out, "%f ", c[i * SIZE + j]);
	}
      fprintf (out, "\n");
    }
}

int
main (int argc, char *argv[])
{
  int i;
  int points, var;

  if (argc == 1)
    {
      return;
    }
  points = atoi (argv[1]);
  var = SIZE / points;

  fil = fopen ("time_gpu.csv", "w+");
  out = fopen ("result_gpu.txt", "w+");

  fprintf (fil, "SIZE,matrix sum gpu,\n");


  for (i = (var - 1); i < SIZE; i += var)
    {
      init (i);
      fprintf (fil, "%d,", i);
      sum_GPU (i);
      print ();
      fprintf (fil, "\n");
    }
  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (float *a, float *c, float *b, int s)
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
		for (j = 0; j < s; ++j)
		  {
		    c[i * s + j] = a[i * s + j] + b[i * s + j];
		  }
	      }

	  }
	}
      }
    }
  }
}

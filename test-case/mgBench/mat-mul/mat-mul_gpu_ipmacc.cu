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

int SIZE;




float *a;
float *b;
float *c;

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
	  a[i * s + j] = (float) i + j % 100;
	  b[i * s + j] = (float) i + j % 100;
	  c[i * s + j] = 0.0f;
	}
    }
}


void
print (int s)
{
  int i, j;
  for (i = 0; i < s; ++i)
    {
      for (j = 0; j < s; ++j)
	{
	  fprintf (out, "%f ", c[i * s + j]);
	}
      fprintf (out, "\n");
    }
}



__global__ void __generated_kernel_region_0 (float *a, float *c, float *b,
					     int s, float sum);

void
mul_GPU (int s)
{
  int i, j, k, l;
  l = s * s;
  float sum = 0.0;
  float start, finish, elapsed;
  start = (float) clock () / (CLOCKS_PER_SEC * 1000);
  a = (float *) malloc (sizeof (float) * SIZE * SIZE);
  b = (float *) malloc (sizeof (float) * SIZE * SIZE);
  c = (float *) malloc (sizeof (float) * SIZE * SIZE);
  init (SIZE);


  ipmacc_prompt ((char *) "IPMACC: memory allocation c\n");
  acc_create ((void *) c, (l + 0) * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory allocation a\n");
  acc_create ((void *) a, (l + 0) * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory allocation b\n");
  acc_create ((void *) b, (l + 0) * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin c\n");
  acc_copyin ((void *) c, (l + 0) * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin a\n");
  acc_copyin ((void *) a, (l + 0) * sizeof (float));
  ipmacc_prompt ((char *) "IPMACC: memory copyin b\n");
  acc_copyin ((void *) b, (l + 0) * sizeof (float));


  {


    {



/* kernel call statement [0, -1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		(((abs (((s)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_0 <<< (((abs (((s)) - 0)) / (1))) / 256 + 1,
	256 >>> ((float *) acc_deviceptr ((void *) a),
		 (float *) acc_deviceptr ((void *) c),
		 (float *) acc_deviceptr ((void *) b), s, sum);
/* kernel call statement*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();



    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout c\n");
  acc_copyout_and_keep ((void *) c, (l + 0) * sizeof (float));



  acc_free (a);
  acc_free (b);
  acc_free (c);
  finish = (float) clock () / (CLOCKS_PER_SEC * 1000);
  elapsed = finish - start;
  fprintf (fil, "%.10lf,", elapsed);
  print (s);
  free (a);
  free (b);
  free (c);
}

int
main (int argc, char *argv[])
{
  int i;
  int points, var, limit;

  if (argc != 2)
    {
      return;
    }
  SIZE = atoi (argv[1]);




  fil = fopen ("time_gpu.csv", "a");
  out = fopen ("result_gpu.txt", "a");

  fprintf (fil, "SIZE,matrix multiplication GPU,\n");



  {

    printf ("i: %d\n", SIZE);




    fprintf (fil, "%d,", SIZE);
    mul_GPU (SIZE);

    fprintf (fil, "\n");



  }
  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (float *a, float *c, float *b, int s, float sum)
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
	    i = 0 + (__kernel_getuid);
	    if (i < s)
	      {
		for (j = 0; j < s; ++j)
		  {
		    sum = 0.0;
		    for (k = 0; k < s; ++k)
		      {
			sum = sum + a[i * s + k] * b[k * s + j];
		      }
		    c[i * s + j] = sum;
		  }
	      }

	  }
	}
      }
    }
  }
}

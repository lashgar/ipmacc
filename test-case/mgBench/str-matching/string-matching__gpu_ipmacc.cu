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
#include <math.h>
#include <limits.h>
#include <string.h>
#include <openacc.h>
#include <time.h>

#define SIZE 500000

char frase[SIZE];
char palavra[SIZE];

FILE *fil;
FILE *out;


int
init (int s, int p)
{
  int i;
  for (i = 0; i < s; i++)
    {
      frase[i] = 'a';
    }
  frase[i] = '\0';
  for (i = 0; i < p; i++)
    {
      palavra[i] = 'a';
    }
  palavra[i] = '\0';
}




__global__ void __generated_kernel_region_0 (char *frase, int *vector,
					     int parallel_size, int diff,
					     char *palavra, int size_2);

int
string_matching_GPU (int size_1, int size_2)
{
  int i, diff, j, parallel_size, count = 0;
  diff = size_1 - size_2;

  float start, finish, elapsed;
  start = (float) clock () / (CLOCKS_PER_SEC * 1000);
  parallel_size = 100000;
  int vector[parallel_size];
  for (i = 0; i < parallel_size; i++)
    {
      vector[i] = 0;
    }


  ipmacc_prompt ((char *) "IPMACC: memory allocation vector\n");
  acc_create ((void *) vector, parallel_size * sizeof (int));
  ipmacc_prompt ((char *) "IPMACC: memory allocation frase\n");
  acc_create ((void *) frase, SIZE * sizeof (char));
  ipmacc_prompt ((char *) "IPMACC: memory allocation palavra\n");
  acc_create ((void *) palavra, SIZE * sizeof (char));
  ipmacc_prompt ((char *) "IPMACC: memory copyin vector\n");
  acc_copyin ((void *) vector, parallel_size * sizeof (int));
  ipmacc_prompt ((char *) "IPMACC: memory copyin frase\n");
  acc_copyin ((void *) frase, SIZE * sizeof (char));
  ipmacc_prompt ((char *) "IPMACC: memory copyin palavra\n");
  acc_copyin ((void *) palavra, SIZE * sizeof (char));


  {


    {



/* kernel call statement [0, -1]*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Launching kernel 0 > gridDim: %d\tblockDim: %d\n",
		(((abs (((diff)) - 0)) / (1))) / 256 + 1, 256);
      __generated_kernel_region_0 <<< (((abs (((diff)) - 0)) / (1))) / 256 +
	1, 256 >>> ((char *) acc_deviceptr ((void *) frase),
		    (int *) acc_deviceptr ((void *) vector), parallel_size,
		    diff, (char *) acc_deviceptr ((void *) palavra), size_2);
/* kernel call statement*/
      if (getenv ("IPMACC_VERBOSE"))
	printf ("IPMACC: Synchronizing the region with host\n");
      cudaDeviceSynchronize ();



    }
  }
  ipmacc_prompt ((char *) "IPMACC: memory copyout vector\n");
  acc_copyout_and_keep ((void *) vector, parallel_size * sizeof (int));



  acc_free (frase);
  acc_free (palavra);
  acc_free (vector);
  for (i = 0; i < parallel_size; i++)
    {
      count += vector[i];
    }
  finish = (float) clock () / (CLOCKS_PER_SEC * 1000);
  elapsed = finish - start;
  fprintf (fil, "%.6lf,", elapsed);
  return count;
}

int
main (int argc, char *argv[])
{
  int i, j, k;
  int points, var;
  if (argc == 1)
    {
      return;
    }
  points = atoi (argv[1]);
  var = SIZE / points;

  fil = fopen ("time_gpu.csv", "w+");
  out = fopen ("result_gpu.txt", "w+");

  fprintf (fil, "Size string,Size substring,String Matching GPU,\n");

  for (i = (var - 1); i < SIZE; i += var)
    {
      j = i / 2;
      fprintf (fil, "%d,", i);
      fprintf (fil, "%d,", j);
      init (i, j);
      k = string_matching_GPU (i, j);
      fprintf (out, "%d\n", k);
      fprintf (fil, "\n");
    }
  fclose (fil);
  fclose (out);
  return 0;
}



__global__ void
__generated_kernel_region_0 (char *frase, int *vector, int parallel_size,
			     int diff, char *palavra, int size_2)
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
	    if (i < diff)
	      {
		int v;
		v = 0;
		for (j = 0; j < size_2; j++)
		  {
		    if (frase[(i + j)] != palavra[j])
		      {
			v = 1;
		      }
		  }
		if (v == 0)
		  {
		    vector[i % parallel_size]++;
		  }
	      }

	  }
	}
      }
    }
  }
}

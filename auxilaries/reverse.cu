float **__autogen_device_main_c;
short __autogen_device_main_c_prstn = 0;
float **__autogen_device_main_a;
short __autogen_device_main_a_prstn = 0;
float **__autogen_device_main_b;
short __autogen_device_main_b_prstn = 0;

#include <malloc.h>
#include <time.h>
#include <openacc.h>

#include <math.h>

#define SIZE 1000
int
main ()
{
  int i, j;

  float a[SIZE][SIZE];
  float b[SIZE][SIZE];
  float c[SIZE][SIZE];
  float seq[SIZE][SIZE];
  acc_init (acc_device_nvidia);



  for (i = 0; i < SIZE; ++i)
    {

      for (j = 0; j < SIZE; ++j)
	{

	  a[i][j] = (float) i + j;
	  b[i][j] = (float) i - j;
	  c[i][j] = 0.0f;
	}
    }

  unsigned long long int tic, toc;

  int k;
  for (k = 0; k < 3; k++)
    {

      printf ("Calculation on GPU ... ");
      tic = clock ();


      if (!__autogen_device_main_c_prstn)
	{
	  __autogen_device_main_c_prstn++;
	  cudaMalloc ((void **) &c, (1000) * (1000) * sizeof (float));
	}
      cudaMemcpy (__autogen_device_main_c, c,
		  (1000) * (1000) * sizeof (float), cudaMemcpyHostToDevice);
      if (!__autogen_device_main_a_prstn)
	{
	  __autogen_device_main_a_prstn++;
	  cudaMalloc ((void **) &a, (1000) * (1000) * sizeof (float));
	}
      cudaMemcpy (__autogen_device_main_a, a,
		  (1000) * (1000) * sizeof (float), cudaMemcpyHostToDevice);
      if (!__autogen_device_main_b_prstn)
	{
	  __autogen_device_main_b_prstn++;
	  cudaMalloc ((void **) &b, (1000) * (1000) * sizeof (float));
	}
      cudaMemcpy (__autogen_device_main_b, b,
		  (1000) * (1000) * sizeof (float), cudaMemcpyHostToDevice);


      {

	__ungenerated_kernel_region_0 ();

      }
      cudaMemcpy (c, __autogen_device_main_c,
		  (1000) * (1000) * sizeof (float), cudaMemcpyDeviceToHost);


      toc = clock ();
      printf (" %6.4f ms\n", (toc - tic) / (float) 1000);
    }





  printf ("Calculation on CPU ... ");
  tic = clock ();
  for (i = 0; i < SIZE; ++i)
    {

      for (j = 0; j < SIZE; ++j)
	{

	  seq[i][j] = sin (a[i][j]) + cos (b[i][j]) + cos (a[i][j] * b[i][j]);
	  if (c[i][j] != seq[i][j])
	    {
	      printf ("Error %d %d\n", i, j);
	      exit (1);
	    }
	}
    }
  toc = clock ();
  printf (" %6.4f ms\n", (toc - tic) / (float) 1000);

  printf ("OpenACC vector add test was successful!\n");

  return 0;
}

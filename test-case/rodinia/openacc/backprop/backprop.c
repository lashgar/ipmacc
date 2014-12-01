/*
 ******************************************************************
 * HISTORY
 * 15-Oct-94  Jeff Shufelt (js), Carnegie Mellon University
 *	Prepared for 15-681, Fall 1994.
 * Modified by Shuai Che
 ******************************************************************
 */

#include <stdio.h>
#include <stdlib.h>
#include "backprop.h"
#include <math.h>
#include <fcntl.h>
#include <unistd.h>

#define ABS(x)          (((x) > 0.0) ? (x) : (-(x)))

#define fastcopy(to,from,len)\
{\
  register char *_to,*_from;\
  register int _i,_l;\
  _to = (char *)(to);\
  _from = (char *)(from);\
  _l = (len);\
  for (_i = 0; _i < _l; _i++) *_to++ = *_from++;\
}

/*** The squashing function.  Currently, it's a sigmoid. ***/

#define SQUASH(x)       (1.0 / (1.0 + exp(-x)))


/*** Return random number between 0.0 and 1.0 ***/
float drnd()
{
  return ((float) rand() / (float) BIGRND);
}

/*** Return random number between -1.0 and 1.0 ***/
float dpn1()
{
  return ((drnd() * 2.0) - 1.0);
}


/*** Allocate 1d array of floats ***/

float *alloc_1d_dbl(int n)
{
  float *newm;

  newm = (float *) malloc ((unsigned) (n * sizeof (float)));
  if (newm == NULL) {
    printf("ALLOC_1D_DBL: Couldn't allocate array of floats\n");
    return (NULL);
  }
  return (newm);
}


/*** Allocate contiguous 2d array of floats ***/

float **alloc_2d_dbl(int m, int n)
{
  int i;
  float **new2;

  new2 = (float **) malloc ((unsigned) (m * sizeof (float *)));
  if (new2 == NULL) {
    printf("ALLOC_2D_DBL: Couldn't allocate array of dbl ptrs\n");
    return (NULL);
  }

  new2[0] = (float *) malloc ((unsigned) (m * n * sizeof (float)));
  for (i = 1 ; i < m; i++) {
    new2[i] = new2[i-1] + n;
  }

  return (new2);
}


/*** Deallocate contiguous 2d array ***/

void free_2d(float **mem)
{
    free((float *)mem[0]);
}


void bpnn_randomize_weights(float *w, int m, int n)
{
  int i, j;

  for (i = 0; i <= m; i++) {
    for (j = 0; j <= n; j++) {
     w[i*n+j] = (float) rand()/RAND_MAX;
    //  w[i][j] = dpn1();
    }
  }
}

void bpnn_randomize_row(float *w, int m)
{
	int i;
	for (i = 0; i <= m; i++) {
     //w[i] = (float) rand()/RAND_MAX;
	 w[i] = 0.1;
    }
}


void bpnn_zero_weights(float *w, int m, int n)
{
  int i, j;

  for (i = 0; i <= m; i++) {
    for (j = 0; j <= n; j++) {
      w[i*n+j] = 0.0;
    }
  }
}


void bpnn_initialize(int seed)
{
  printf("Random number generator seed: %d\n", seed);
  srand(seed);
}


BPNN *bpnn_internal_create(int n_in, int n_hidden, int n_out)
{
  BPNN *newnet;

  newnet = (BPNN *) malloc (sizeof (BPNN));
  if (newnet == NULL) {
    printf("BPNN_CREATE: Couldn't allocate neural network\n");
    return (NULL);
  }

  newnet->input_n = n_in;
  newnet->hidden_n = n_hidden;
  newnet->output_n = n_out;
  newnet->input_units = alloc_1d_dbl(n_in + 1);
  newnet->hidden_units = alloc_1d_dbl(n_hidden + 1);
  newnet->output_units = alloc_1d_dbl(n_out + 1);

  newnet->hidden_delta = alloc_1d_dbl(n_hidden + 1);
  newnet->output_delta = alloc_1d_dbl(n_out + 1);
  newnet->target = alloc_1d_dbl(n_out + 1);

  newnet->input_weights = alloc_1d_dbl((n_in + 1)*(n_hidden + 1));
  //newnet->input_weights = alloc_2d_dbl(n_in + 1, n_hidden + 1);
  newnet->hidden_weights = alloc_1d_dbl((n_hidden + 1)*( n_out + 1));
  //newnet->hidden_weights = alloc_2d_dbl(n_hidden + 1, n_out + 1);

  newnet->input_prev_weights = alloc_1d_dbl((n_in + 1)*(n_hidden + 1));
  //newnet->input_prev_weights = alloc_2d_dbl(n_in + 1, n_hidden + 1);
  newnet->hidden_prev_weights = alloc_1d_dbl((n_hidden + 1)*( n_out + 1));
  //newnet->hidden_prev_weights = alloc_2d_dbl(n_hidden + 1, n_out + 1);

  return (newnet);
}


void bpnn_free(BPNN *net)
{
  int n1, n2, i;

  n1 = net->input_n;
  n2 = net->hidden_n;

  free((char *) net->input_units);
  free((char *) net->hidden_units);
  free((char *) net->output_units);

  free((char *) net->hidden_delta);
  free((char *) net->output_delta);
  free((char *) net->target);

  free((char*)net->input_weights);
  free((char*)net->input_prev_weights);
  free((char*)net->hidden_weights);
  free((char*)net->hidden_prev_weights);

//  free((char *) net->hidden_weights);
//  free((char *) net->hidden_prev_weights);

  free((char *) net);
}

  
/*** Creates a new fully-connected network from scratch,
     with the given numbers of input, hidden, and output units.
     Threshold units are automatically included.  All weights are
     randomly initialized.

     Space is also allocated for temporary storage (momentum weights,
     error computations, etc).
***/

BPNN *bpnn_create(int n_in, int n_hidden, int n_out)
{

  BPNN *newnet;

  newnet = bpnn_internal_create(n_in, n_hidden, n_out);

#ifdef INITZERO
  bpnn_zero_weights(newnet->input_weights, n_in, n_hidden);
#else
  bpnn_randomize_weights(newnet->input_weights, n_in, n_hidden);
#endif
  bpnn_randomize_weights(newnet->hidden_weights, n_hidden, n_out);
  bpnn_zero_weights(newnet->input_prev_weights, n_in, n_hidden);
  bpnn_zero_weights(newnet->hidden_prev_weights, n_hidden, n_out);
  bpnn_randomize_row(newnet->target, n_out);
  return (newnet);
}


void bpnn_layerforward(float *l1, float *l2, float *conn, int n1, int n2)
{
  float sum;
  int j, k;

  /*** Set up thresholding unit ***/
  //#pragma acc kernels present(l1)
  l1[0] = 1.0;

  #pragma acc kernels present(l1,l2,conn)
    #pragma acc loop independent
  /*** For each unit in second layer ***/
  for (j = 1; j <= n2; j++) {

    /*** Compute weighted sum of its inputs ***/
    sum = 0.0;
    #pragma acc loop independent reduction(+:sum)
    for (k = 0; k <= n1; k++) {	
      //sum += conn[k][j] * l1[k]; 
      sum += conn[k*n2+j] * l1[k]; 
    }
    l2[j] = SQUASH(sum);
  }
}


void bpnn_output_error(float *delta, float *target, float *output, int nj, float *err)
{
  int j;
  float o, t, errsum;
  errsum = 0.0;
  #pragma acc kernels present(delta,target,output)
  #pragma acc loop independent reduction(+:errsum)
  for (j = 1; j <= nj; j++) {
    o = output[j];
    t = target[j];
    delta[j] = o * (1.0 - o) * (t - o);
    errsum += ABS(delta[j]);
  }
  *err = errsum;
}


void bpnn_hidden_error(float *delta_h,   
					   int nh, 
					   float *delta_o, 
					   int no, 
					   float *who, 
					   float *hidden, 
					   float *err)
{
  int j, k;
  float h, sum, errsum;

  errsum = 0.0;
  #pragma acc kernels present(delta_h,delta_o,who,hidden)
  #pragma acc loop independent reduction(+:errsum)
  for (j = 1; j <= nh; j++) {
    h = hidden[j];
    sum = 0.0;
    #pragma acc loop reduction(+:sum)
    for (k = 1; k <= no; k++) {
      sum += delta_o[k] * who[j*no+k];
    }
    delta_h[j] = h * (1.0 - h) * sum;
    errsum += ABS(delta_h[j]);
  }
  *err = errsum;
}


void bpnn_adjust_weights(float *delta, int ndelta, float *ly, int nly, float *w, float *oldw)
{
  float new_dw;
  int k, j;
  ly[0] = 1.0;
  //eta = 0.3;
  //momentum = 0.3;

  #pragma acc kernels present(delta,ly,w,oldw)
    #pragma acc loop independent
  for (j = 1; j <= ndelta; j++) {
    #pragma acc loop independent
    for (k = 0; k <= nly; k++) {
      new_dw = ((ETA * delta[j] * ly[k]) + (MOMENTUM * oldw[j*nly+k]));
	  w[k*ndelta+j] += new_dw;
	  oldw[k*ndelta+j] = new_dw;
    }
  }
}


void bpnn_feedforward(BPNN *net)
{
  int in, hid, out;

  in = net->input_n;
  hid = net->hidden_n;
  out = net->output_n;

  /*** Feed forward input activations. ***/
  bpnn_layerforward(net->input_units, net->hidden_units,
      net->input_weights, in, hid);
  bpnn_layerforward(net->hidden_units, net->output_units,
      net->hidden_weights, hid, out);

}


void bpnn_train(BPNN *net, float *eo, float *eh)
{
  int in, hid, out;
  float out_err, hid_err;

  in = net->input_n;
  hid = net->hidden_n;
  out = net->output_n;

  /*** Feed forward input activations. ***/
  bpnn_layerforward(net->input_units, net->hidden_units,
      net->input_weights, in, hid);
  bpnn_layerforward(net->hidden_units, net->output_units,
      net->hidden_weights, hid, out);

  /*** Compute error on output and hidden units. ***/
  bpnn_output_error(net->output_delta, net->target, net->output_units,
      out, &out_err);
  bpnn_hidden_error(net->hidden_delta, hid, net->output_delta, out,
      net->hidden_weights, net->hidden_units, &hid_err);
  *eo = out_err;
  *eh = hid_err;

  /*** Adjust input and hidden weights. ***/
  bpnn_adjust_weights(net->output_delta, out, net->hidden_units, hid,
      net->hidden_weights, net->hidden_prev_weights);
  bpnn_adjust_weights(net->hidden_delta, hid, net->input_units, in,
      net->input_weights, net->input_prev_weights);

}




void bpnn_save(BPNN *net, char *filename)
{
  int n1, n2, n3, i, j, memcnt;
  float dvalue, *w;
  char *mem;
  ///add//
  FILE *pFile;
  pFile = fopen( filename, "w+" );
  ///////
  /*
  if ((fd = creat(filename, 0644)) == -1) {
    printf("BPNN_SAVE: Cannot create '%s'\n", filename);
    return;
  }
  */

  n1 = net->input_n;  n2 = net->hidden_n;  n3 = net->output_n;
  printf("Saving %dx%dx%d network to '%s'\n", n1, n2, n3, filename);
  //fflush(stdout);

  //write(fd, (char *) &n1, sizeof(int));
  //write(fd, (char *) &n2, sizeof(int));
  //write(fd, (char *) &n3, sizeof(int));

  fwrite( (char *) &n1 , sizeof(char), sizeof(char), pFile);
  fwrite( (char *) &n2 , sizeof(char), sizeof(char), pFile);
  fwrite( (char *) &n3 , sizeof(char), sizeof(char), pFile);

  

  memcnt = 0;
  w = net->input_weights;
  mem = (char *) malloc ((unsigned) ((n1+1) * (n2+1) * sizeof(float)));
  for (i = 0; i <= n1; i++) {
    for (j = 0; j <= n2; j++) {
      dvalue = w[i*n2+j];
      fastcopy(&mem[memcnt], &dvalue, sizeof(float));
      memcnt += sizeof(float);
    }
  }
  //write(fd, mem, (n1+1) * (n2+1) * sizeof(float));
  fwrite( mem , (unsigned)(sizeof(float)), (unsigned) ((n1+1) * (n2+1) * sizeof(float)) , pFile);
  free(mem);

  memcnt = 0;
  w = net->hidden_weights;
  mem = (char *) malloc ((unsigned) ((n2+1) * (n3+1) * sizeof(float)));
  for (i = 0; i <= n2; i++) {
    for (j = 0; j <= n3; j++) {
      dvalue = w[i*n3+j];
      fastcopy(&mem[memcnt], &dvalue, sizeof(float));
      memcnt += sizeof(float);
    }
  }
  //write(fd, mem, (n2+1) * (n3+1) * sizeof(float));
  fwrite( mem , sizeof(float), (unsigned) ((n2+1) * (n3+1) * sizeof(float)) , pFile);
  free(mem);

  fclose(pFile);
  return;
}


BPNN *bpnn_read(char *filename)
{
  char *mem;
  BPNN *new2;
  int fd, n1, n2, n3, i, j, memcnt;

  if ((fd = open(filename, 0, 0644)) == -1) {
    return (NULL);
  }

  printf("Reading '%s'\n", filename);  //fflush(stdout);

  read(fd, (char *) &n1, sizeof(int));
  read(fd, (char *) &n2, sizeof(int));
  read(fd, (char *) &n3, sizeof(int));
  new2 = bpnn_internal_create(n1, n2, n3);

  printf("'%s' contains a %dx%dx%d network\n", filename, n1, n2, n3);
  printf("Reading input weights...");  //fflush(stdout);

  memcnt = 0;
  mem = (char *) malloc ((unsigned) ((n1+1) * (n2+1) * sizeof(float)));
  read(fd, mem, (n1+1) * (n2+1) * sizeof(float));
  for (i = 0; i <= n1; i++) {
    for (j = 0; j <= n2; j++) {
      fastcopy(&(new2->input_weights[i*n2+j]), &mem[memcnt], sizeof(float));
      memcnt += sizeof(float);
    }
  }
  free(mem);

  printf("Done\nReading hidden weights...");  //fflush(stdout);

  memcnt = 0;
  mem = (char *) malloc ((unsigned) ((n2+1) * (n3+1) * sizeof(float)));
  read(fd, mem, (n2+1) * (n3+1) * sizeof(float));
  for (i = 0; i <= n2; i++) {
    for (j = 0; j <= n3; j++) {
      fastcopy(&(new2->hidden_weights[i*n3+j]), &mem[memcnt], sizeof(float));
      memcnt += sizeof(float);
    }
  }
  free(mem);
  close(fd);

  printf("Done\n");  //fflush(stdout);

  bpnn_zero_weights(new2->input_prev_weights, n1, n2);
  bpnn_zero_weights(new2->hidden_prev_weights, n2, n3);

  return (new2);
}

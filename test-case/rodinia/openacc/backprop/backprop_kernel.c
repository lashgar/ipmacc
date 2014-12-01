#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>

#include "backprop.h"

////////////////////////////////////////////////////////////////////////////////

extern void bpnn_layerforward(float *l1, float *l2, float *conn, int n1, int n2);

extern void bpnn_output_error(float *delta, float *target, float *output, int nj, float *err);

extern void bpnn_hidden_error(float *delta_h, int nh, float *delta_o, int no, float *who, float *hidden, float *err);

extern void bpnn_adjust_weights(float *delta, int ndelta, float *ly, int nly, float *w, float *oldw);


extern int setup(int argc, char** argv);

extern float **alloc_2d_dbl(int m, int n);

extern float squash(float x);

double gettime() {
  struct timeval t;
  gettimeofday(&t,NULL);
  return t.tv_sec+t.tv_usec*1e-6;
}

////////////////////////////////////////////////////////////////////////////////
// Program main
////////////////////////////////////////////////////////////////////////////////
int
main( int argc, char** argv) 
{
    #ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
    #endif 
    #ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
    #endif 



	setup(argc, argv);
}


void bpnn_train_kernel(BPNN *net, float *eo, float *eh)
{
  int in, hid, out;
  float out_err, hid_err;
  float *input_units, *hidden_units, *output_units;
  float *target, *hidden_delta, *output_delta;
  float *input_weights, *hidden_weights;
  float *hidden_prev_weights, *input_prev_weights;
  
  in = net->input_n;
  hid = net->hidden_n;
  out = net->output_n;   

  input_units = net->input_units;
  hidden_units = net->hidden_units;
  output_units = net->output_units;

  input_weights = net->input_weights;
  hidden_weights = net->hidden_weights;

  target = net->target;
  hidden_delta = net->hidden_delta;
  output_delta = net->output_delta;

  hidden_prev_weights = net->hidden_prev_weights;
  input_prev_weights = net->input_prev_weights;

#pragma acc data copyin(input_units[0:in]) \
  create(hidden_units[0:hid], output_units[0:out]) \
  create(input_weights[0:(in*hid)], hidden_weights[0:(hid*out)]) \
  create(hidden_delta[0:hid], output_delta[0:out]) \
  create(input_prev_weights[0:(in*hid)], hidden_prev_weights[0:(hid*out)]) \
  copyin(target[0:out])
{
  printf("Performing CPU computation\n");
  bpnn_layerforward(input_units, hidden_units, input_weights, in, hid);
  bpnn_layerforward(hidden_units, output_units, hidden_weights, hid, out);
  bpnn_output_error(output_delta, target, output_units, out, &out_err);
  bpnn_hidden_error(hidden_delta, hid, output_delta, out, hidden_weights, hidden_units, &hid_err);
  bpnn_adjust_weights(output_delta, out, hidden_units, hid, hidden_weights, hidden_prev_weights);
  bpnn_adjust_weights(hidden_delta, hid, input_units, in, input_weights, input_prev_weights);
} /* end acc data */

}

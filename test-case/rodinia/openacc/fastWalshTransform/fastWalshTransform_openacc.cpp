
////////////////////////////////////////////////////////////////////////////////
// Reference CPU dyadic convolution.
// Extremly slow because of non-linear memory access patterns (cache thrashing)
////////////////////////////////////////////////////////////////////////////////
extern int   dataN;
extern int kernelN;

void dyadicConvolutionCPU_openacc(
    float *h_Result_f,
    float *h_Data_f,
    float *h_Kernel_f,
    int log2dataN,
    int log2kernelN)
{
    //printf("memory size> %d\n",dataN);
    //printf("memory size> %d\n",kernelN);
    const int   dataNL = 1 << log2dataN;
    const int kernelNL = 1 << log2kernelN;

    float *h_Result=(float*)h_Result_f;
    float *h_Data  =(float*)h_Data_f;
    float *h_Kernel=(float*)h_Kernel_f;

    #pragma acc kernels pcopyin(h_Data[0:dataN],h_Kernel[0:kernelN]) pcopyout(h_Result[0:dataN])
    #pragma acc loop independent 
    for (int i = 0; i < dataNL; i++)
    {
        double sum = 0;
        for (int j = 0; j < kernelNL; j++){
            sum += h_Data[i ^ j] * h_Kernel[j];
        }
        h_Result[i] = (float)sum;
    }
}

///////////////////////////////////////////////////////////////////////////////
// CPU Fast Walsh Transform
///////////////////////////////////////////////////////////////////////////////
void fwtCPU_openacc(float *h_Output_f, float *h_Input_f, int log2N)
{
    const int N = 1 << log2N;
    float *h_Output  =(float*)h_Output_f;
    float *h_Input  =(float*)h_Input_f;

    for (int pos = 0; pos < N; pos++)
        h_Output[pos] = h_Input[pos];

    int stride, baseI, base;
    //Cycle through stages with different butterfly strides
    #pragma acc data pcopyout(h_Output[0:dataN]) pcopyin(h_Input[0:dataN])
    for (stride = N / 2; stride >= 1; stride >>= 1)
    {
        printf("calling %d\n",stride);
        //Cycle through subvectors of (2 * stride) elements
        if(stride>128){
            for (baseI = 0; baseI < (N/(2*stride)+1); baseI++)
            //for (base = 0; base < N; base += 2 * stride)
            {
                base=baseI*2*stride;
                if(base<N)
                {
                    #pragma acc kernels present(h_Output,h_Input)
                    #pragma acc loop independent 
                    for (int j = 0; j < stride; j++)
                    {
                        //Butterfly index within subvector of (2 * stride) size
                        int i0 = base + j +      0;
                        int i1 = base + j + stride;

                        float T1 = h_Output[i0];
                        float T2 = h_Output[i1];
                        h_Output[i0] = T1 + T2;
                        h_Output[i1] = T1 - T2;
                    }
                }
            }
        }else{
            #pragma acc kernels present(h_Output,h_Input)
            #pragma acc loop independent 
            for (baseI = 0; baseI < (N/(2*stride)+1); baseI++)
            //for (base = 0; base < N; base += 2 * stride)
            {
                base=baseI*2*stride;
                if(base<N)
                {
                    for (int j = 0; j < stride; j++)
                    {
                        //Butterfly index within subvector of (2 * stride) size
                        int i0 = base + j +      0;
                        int i1 = base + j + stride;

                        float T1 = h_Output[i0];
                        float T2 = h_Output[i1];
                        h_Output[i0] = T1 + T2;
                        h_Output[i1] = T1 - T2;
                    }
                }
            }
        }
    }
}



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
#include <sys/time.h>
using namespace std;
#define STR_SIZE  256


#define MAX_PD  (3.0e6)

#define PRECISION 0.001
#define SPEC_HEAT_SI 1.75e6
#define K_SI 100

#define FACTOR_CHIP 0.5


double t_chip = 0.0005;
double chip_height = 0.016;
double chip_width = 0.016;

double amb_temp = 80.0;
#define BLOCKSIZEX 16 
#define BLOCKSIZEY 16 
#define BLOCKSIZEXLOG 4
#define BLOCKSIZEYLOG 4


bool INRANGE(int rid, int cid, int iter, int innerIter, int tiler, int tilec, int blockdimr, int blockdimc)
{
    int localdimr = (blockdimr);
    int localdimc = (blockdimc);
    int localr = rid & (localdimr - 1);
    int localc = cid & (localdimc - 1);
    return ((localr > iter) && (localc > iter)) &&
        ((localr < (blockdimr - iter - 1)) && (localc < (blockdimc - iter - 1)));
}

__device__ bool __accelerator_INRANGE( int rid , int cid , int iter , int innerIter , int tiler , int tilec , int blockdimr , int blockdimc );
__global__ void __generated_kernel_region_0(double amb_temp,int dimrow,double* result,int row,int innerIter,double* power,int dimcol,double rRx,double stepCap,double delta,double* temp,double rRz,double rRy,int col);

void single_iteration(double *result, double *temp, double *power, int row, int col,
        double Cap, double Rx, double Ry, double Rz,
        double step, int innerIter, int *written)
{
    double delta;
    double stepCap = step / Cap;
    double rRx = 1 / Rx;
    double rRy = 1 / Ry;
    double rRz = 1 / Rz;
    int rs, cs;
#define TILEX (BLOCKSIZEX - 2 * innerIter)
#define TILEY (BLOCKSIZEY - 2 * innerIter)

    int dimrow = (row + ((2 * innerIter) * (row / TILEX + 1)));
    int dimcol = (col + ((2 * innerIter) * (col / TILEY + 1)));



    ipmacc_prompt((char*)"IPMACC: memory getting device pointer for temp\n");
    acc_present((void*)temp);
    ipmacc_prompt((char*)"IPMACC: memory getting device pointer for power\n");
    acc_present((void*)power);
    ipmacc_prompt((char*)"IPMACC: memory getting device pointer for result\n");
    acc_present((void*)result);
    ipmacc_prompt((char*)"IPMACC: memory getting device pointer for written\n");
    acc_present((void*)written);

    /* kernel call statement [0]*/
    {
        dim3 __ipmacc_gridDim(1,1,1);
        dim3 __ipmacc_blockDim(1,1,1);
        __ipmacc_blockDim.x=16;
        __ipmacc_gridDim.x=(((abs((int)((dimcol))-0))/(1))/__ipmacc_blockDim.x)+1;
        __ipmacc_blockDim.y=16;
        __ipmacc_gridDim.y=(((abs((int)((dimrow))-0))/(1))/__ipmacc_blockDim.y)+1;
        if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Launching kernel 0 > gridDim: (%u,%u,%u)\tblockDim: (%u,%u,%u)\n",__ipmacc_gridDim.x,__ipmacc_gridDim.y,__ipmacc_gridDim.z,__ipmacc_blockDim.x,__ipmacc_blockDim.y,__ipmacc_blockDim.z);
        __generated_kernel_region_0<<<__ipmacc_gridDim,__ipmacc_blockDim>>>(
                amb_temp,
                dimrow,
                (double*)acc_deviceptr((void*)result),
                row,
                innerIter,
                (double*)acc_deviceptr((void*)power),
                dimcol,
                rRx,
                stepCap,
                delta,
                (double*)acc_deviceptr((void*)temp),
                rRz,
                rRy,
                col);
    }
    /* kernel call statement*/
    if (getenv("IPMACC_VERBOSE")) printf("IPMACC: Synchronizing the region with host\n");
    {
        cudaError err=cudaDeviceSynchronize();
        if(err!=cudaSuccess){
            printf("Kernel Launch Error! error code (%d)\n",err);
            assert(0&&"Launch Failure!\n");}
    }














}


void compute_tran_temp(double *result, int num_iterations, double *temp, double *power, int row, int col, int inner_iter, int *written)
{
#ifdef VERBOSE
    int i = 0;
#endif

    double grid_height = chip_height / row;
    double grid_width = chip_width / col;

    double Cap = FACTOR_CHIP * SPEC_HEAT_SI * t_chip * grid_width * grid_height;
    double Rx = grid_width / (2.0 * K_SI * t_chip * grid_height);
    double Ry = grid_height / (2.0 * K_SI * t_chip * grid_width);
    double Rz = t_chip / (K_SI * grid_height * grid_width);

    double max_slope = MAX_PD / (FACTOR_CHIP * t_chip * SPEC_HEAT_SI);
    double step = PRECISION / max_slope;

#ifdef VERBOSE
    fprintf(stdout, "total iterations: %d s\tstep size: %g s\n", num_iterations, step);
    fprintf(stdout, "Rx: %g\tRy: %g\tRz: %g\tCap: %g\n", Rx, Ry, Rz, Cap);
#endif



    ipmacc_prompt((char*)"IPMACC: memory allocation temp\n");
    acc_create((void*)temp,(row*col+0)*sizeof(double));
    ipmacc_prompt((char*)"IPMACC: memory allocation written\n");
    acc_create((void*)written,(row*col+0)*sizeof(int));
    ipmacc_prompt((char*)"IPMACC: memory allocation power\n");
    acc_create((void*)power,(row*col+0)*sizeof(double));
    ipmacc_prompt((char*)"IPMACC: memory allocation result\n");
    acc_create((void*)result,(row*col+0)*sizeof(double));
    ipmacc_prompt((char*)"IPMACC: memory copyin temp\n");
    acc_copyin((void*)temp,(row*col+0)*sizeof(double));
    ipmacc_prompt((char*)"IPMACC: memory copyin written\n");
    acc_copyin((void*)written,(row*col+0)*sizeof(int));
    ipmacc_prompt((char*)"IPMACC: memory copyin power\n");
    acc_copyin((void*)power,(row*col+0)*sizeof(double));


    {


        {

            for(int i = 0; i < num_iterations / inner_iter; i++)
            {
#ifdef VERBOSE
                fprintf(stdout, "iteration %d\n", i++);
#endif
                single_iteration(result, temp, power, row, col, Cap, Rx, Ry, Rz, step, inner_iter, written);
                double *tmp = temp;
                temp = result;
                result = tmp;
            }


        }
    }
    ipmacc_prompt((char*)"IPMACC: memory copyout temp\n");
    acc_copyout_and_keep((void*)temp,(row*col+0)*sizeof(double));
    ipmacc_prompt((char*)"IPMACC: memory copyout written\n");
    acc_copyout_and_keep((void*)written,(row*col+0)*sizeof(int));




#ifdef VERBOSE
    fprintf(stdout, "iteration %d\n", i++);
#endif
}

void fatal(char *s)
{
    fprintf(stderr, "error: %s\n", s);
    exit(1);
}

void read_input(double *vect, int grid_rows, int grid_cols, char *file)
{
    int i;
    FILE *fp;
    char str [STR_SIZE];
    double val;

    fp = fopen(file, "r");
    if (!fp) {
        fatal("file could not be opened for reading");
    }

    for (i = 0; i < grid_rows * grid_cols; i++) {
        fgets(str, STR_SIZE, fp);
        if (feof(fp)) {
            fatal("not enough lines in file");
        }
        if ((sscanf(str, "%lf", &val) != 1)) {
            fatal("invalid file format");
        }
        vect [i] = val;
    }

    fclose(fp);
}

void usage(int argc, char **argv)
{
    fprintf(stderr, "Usage: %s <grid_rows> <grid_cols> <inner_iter> <sim_time> <temp_file> <power_file>\n", argv [0]);
    fprintf(stderr, "\t<grid_rows>  - number of rows in the grid (positive integer)\n");
    fprintf(stderr, "\t<grid_cols>  - number of columns in the grid (positive integer)\n");
    fprintf(stderr, "\t<inner_iter>   - number of iterations within the region\n");
    fprintf(stderr, "\t<sim_time>   - number of iterations\n");
    fprintf(stderr, "\t<temp_file>  - name of the file containing the initial temperature values of each cell\n");
    fprintf(stderr, "\t<power_file> - name of the file containing the dissipated power values of each cell\n");
    exit(1);
}

int main(int argc, char **argv)
{
#ifdef __NVCUDA__
    acc_init(acc_device_nvcuda);
#endif
#ifdef __NVOPENCL__
    acc_init(acc_device_nvocl);

#endif

    int grid_rows, grid_cols, sim_time, inner_iter;
    double *temp, *power, *result;
    int *written;
    char *tfile, *pfile;


    if (argc != 7) {
        usage(argc, argv);
    }
    if ((grid_rows = atoi(argv [1])) <= 0 ||
            (grid_cols = atoi(argv [2])) <= 0 ||
            (sim_time = atoi(argv [4])) <= 0 ||
            (inner_iter = atoi(argv [3])) <= 0
       ) {
        usage(argc, argv);
    }


    temp = (double*)malloc(grid_rows * grid_cols * sizeof(double));
    power = (double*)malloc(grid_rows * grid_cols * sizeof(double));
    result = (double*)malloc(grid_rows * grid_cols * sizeof(double));
    written = (int*)malloc(grid_rows * grid_cols * sizeof(int));
    if (!temp || !power) {
        fatal("unable to allocate memory");
    }


    tfile = argv [5];
    pfile = argv [6];
    read_input(temp, grid_rows, grid_cols, tfile);
    read_input(power, grid_rows, grid_cols, pfile);
    int i;
    for (i = 0; i < grid_rows * grid_cols; i++) {
        written [i] = 0;
    }

    printf("Start computing the transient temperature\n");
    compute_tran_temp(result, sim_time, temp, power, grid_rows, grid_cols, inner_iter, written);
    printf("Ending simulation\n");

#ifdef VERBOSE
    fprintf(stdout, "Final Temperatures:\n");
#endif

#ifdef OUTPUT


    for (i = 0; i < grid_rows * grid_cols; i++) {
        fprintf(stdout, "%d\t%f\n", i, temp [i]);
    }
#endif

    free(temp);
    free(power);

    return 0;
}


__device__ bool __accelerator_INRANGE( int rid , int cid , int iter , int innerIter , int tiler , int tilec , int blockdimr , int blockdimc ) {
    int localdimr  = ( blockdimr ) ; int localdimc  = ( blockdimc ) ; int localr  = rid  & ( localdimr  - 1) ; int localc  = cid  & ( localdimc  - 1) ; return  (( localr  > iter ) && ( localc  > iter )) &&
        (( localr  < ( blockdimr  - iter  - 1)) && ( localc  < ( blockdimc  - iter  - 1))) ; 
}
__forceinline__ __device__ double __smc_select_0_temp(int index, double* g_array, double s_array[16+0+0][16+0+0], int startptr, int startptr2, int dim2size){
    // the pragmas are well-set. do not check the boundaries.
    int idx=index/dim2size;
    int idx2=index%dim2size;
    return s_array[idx-startptr][idx2-startptr2];
}
__forceinline__ __device__ double __smc_select_0_power(int index, double* g_array, double s_array[16+0+0][16+0+0], int startptr, int startptr2, int dim2size){
    // the pragmas are well-set. do not check the boundaries.
    int idx=index/dim2size;
    int idx2=index%dim2size;
    return s_array[idx-startptr][idx2-startptr2];
}

__device__ void __smc_write_0_temp(int index, double* g_array, double s_array[16+0+0][16+0+0], int startptr, int startptr2, int dim2size, double value){
    // the pragmas are well-set. do not check the boundaries.
    int idx=index/dim2size;
    int idx2=index%dim2size;
    s_array[idx-startptr][idx2-startptr2]=value;
}
__device__ void __smc_write_0_power(int index, double* g_array, double s_array[16+0+0][16+0+0], int startptr, int startptr2, int dim2size, double value){
    // the pragmas are well-set. do not check the boundaries.
    int idx=index/dim2size;
    int idx2=index%dim2size;
    s_array[idx-startptr][idx2-startptr2]=value;
}
__global__ void __generated_kernel_region_0(double amb_temp,int dimrow,double* result,int row,int innerIter,double* power,int dimcol,double rRx,double stepCap,double delta,double* temp,double rRz,double rRy,int col){
    int __kernel_getuid_x=threadIdx.x+blockIdx.x*blockDim.x;
    int __kernel_getuid_y=threadIdx.y+blockIdx.y*blockDim.y;
    int __kernel_getuid_z=threadIdx.z+blockIdx.z*blockDim.z;
    int cs;
    int rs;

    /* declare the shared memory of temp */
    __shared__ double __kernel_smc_var_data_temp[16+0+0][16+0+0];
    /*__shared__*/ int __kernel_smc_startpointer_temp;
    /*__shared__*/ int __kernel_smc_endpointer_temp;
    /*__shared__*/ int __kernel_smc_startpointer_temp_2d;
    /*__shared__*/ int __kernel_smc_endpointer_temp_2d;
    __kernel_smc_endpointer_temp=-1;
    __kernel_smc_startpointer_temp=-1;
    __kernel_smc_endpointer_temp_2d=-1;
    __kernel_smc_startpointer_temp_2d=-1;
    /*{
      int iterator_of_smc=0;
      for(iterator_of_smc=threadIdx.x; iterator_of_smc<(16+0+0); iterator_of_smc+=blockDim.x){
    //__kernel_smc_var_data_temp[iterator_of_smc]=0;
    __kernel_smc_var_tag_temp[iterator_of_smc]=0;
    }
    __syncthreads();
    }*/

    /* declare the shared memory of power */
    __shared__ double __kernel_smc_var_data_power[16+0+0][16+0+0];
    /*__shared__*/ int __kernel_smc_startpointer_power;
    /*__shared__*/ int __kernel_smc_endpointer_power;
    /*__shared__*/ int __kernel_smc_startpointer_power_2d;
    /*__shared__*/ int __kernel_smc_endpointer_power_2d;
    __kernel_smc_endpointer_power=-1;
    __kernel_smc_startpointer_power=-1;
    __kernel_smc_endpointer_power_2d=-1;
    __kernel_smc_startpointer_power_2d=-1;
    /*{
      int iterator_of_smc=0;
      for(iterator_of_smc=threadIdx.x; iterator_of_smc<(16+0+0); iterator_of_smc+=blockDim.x){
    //__kernel_smc_var_data_power[iterator_of_smc]=0;
    __kernel_smc_var_tag_power[iterator_of_smc]=0;
    }
    __syncthreads();
    }*/
    {
        {
            {
                rs=0+(__kernel_getuid_y);
                if( rs < dimrow)
                {
                    int r = rs - ((rs >> BLOCKSIZEXLOG) * 2 * innerIter + innerIter);
                    {
                        cs=0+(__kernel_getuid_x);
                        if( cs < dimcol)
                        {
                            int c = cs - ((cs >> BLOCKSIZEYLOG) * 2 * innerIter + innerIter);
                            double new_temp;
                            bool compute = false;

                            {
                                int S = (r == (row - 1)) ? row - 1 : r + 1;
                                int N = (r == (0))    ? 0 : r - 1;
                                int W = (c == (0))    ? 0 : c - 1;
                                int E = (c == (col - 1)) ? col - 1 : c + 1;
                                //go on with the clause (temp[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0],power[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0])
                                { // fetch begins

                                    // FINDING TILE START
                                    __kernel_smc_startpointer_temp=r-0-threadIdx.y;
                                    __kernel_smc_startpointer_temp_2d=c-0-threadIdx.x;

                                    // FINDING DONE

                                    // FINDING TILE END
                                    bool lastcol=blockIdx.x==(gridDim.x-1);
                                    bool lastrow=blockIdx.y==(gridDim.y-1);
                                    __kernel_smc_endpointer_temp=(lastrow)?row-1:blockDim.y+__kernel_smc_startpointer_temp+0-1;
                                    __kernel_smc_endpointer_temp_2d=(lastcol)?col-1:blockDim.x+__kernel_smc_startpointer_temp_2d+0-1;
                                    // FINDING DONE
                                    //__fusion_merge_boundary_0()
                                    __kernel_smc_endpointer_power=     __kernel_smc_endpointer_temp;
                                    __kernel_smc_endpointer_power_2d=  __kernel_smc_endpointer_temp_2d;
                                    __kernel_smc_startpointer_power=   __kernel_smc_startpointer_temp;
                                    __kernel_smc_startpointer_power_2d=__kernel_smc_startpointer_temp_2d;

                                    int __ipmacc_length=__kernel_smc_endpointer_temp-__kernel_smc_startpointer_temp+1;
                                    int __ipmacc_length_2d=__kernel_smc_endpointer_temp_2d-__kernel_smc_startpointer_temp_2d+1;
                                    int kk=0,kk2=0;
                                    kk2=threadIdx.x;
                                    {
                                        int idx2=__kernel_smc_startpointer_temp_2d+kk2;
                                        if(idx2<(col) && idx2>=(0))
                                        {
                                            kk=threadIdx.y;
                                            {
                                                int idx=__kernel_smc_startpointer_temp+kk;
                                                if(idx<(row) && idx>=(0))
                                                {
                                                    __kernel_smc_var_data_temp[kk][kk2]=temp[idx*col+idx2];
                                                    //__kernel_smc_var_tag_temp[kk][kk2]=1;
                                                    //__fusion_merge_fetch_0()
                                                    __kernel_smc_var_data_power[kk][kk2]=power[idx*col+idx2];

                                                }
                                            }
                                        }
                                    }
                                    __syncthreads();
                                } // end of fetch
#define temp(index) __smc_select_0_temp(index, temp, __kernel_smc_var_data_temp, __kernel_smc_startpointer_temp, __kernel_smc_startpointer_temp_2d, col)

                                // 5 unique indexes
                                // [0] S*col+c
#define __ipmacc_smc_index_temp_0_dim1 S-__kernel_smc_startpointer_temp
#define __ipmacc_smc_index_temp_0_dim2 c-__kernel_smc_startpointer_temp_2d
                                // [1] N*col+c
#define __ipmacc_smc_index_temp_1_dim1 N-__kernel_smc_startpointer_temp
#define __ipmacc_smc_index_temp_1_dim2 c-__kernel_smc_startpointer_temp_2d
                                // [2] r*col+c
#define __ipmacc_smc_index_temp_2_dim1 r-__kernel_smc_startpointer_temp
#define __ipmacc_smc_index_temp_2_dim2 c-__kernel_smc_startpointer_temp_2d
                                // [3] r*col+E
#define __ipmacc_smc_index_temp_3_dim1 r-__kernel_smc_startpointer_temp
#define __ipmacc_smc_index_temp_3_dim2 E-__kernel_smc_startpointer_temp_2d
                                // [4] r*col+W
#define __ipmacc_smc_index_temp_4_dim1 r-__kernel_smc_startpointer_temp
#define __ipmacc_smc_index_temp_4_dim2 W-__kernel_smc_startpointer_temp_2d
                                { // fetch begins
                                } // end of fetch
#define power(index) __smc_select_0_power(index, power, __kernel_smc_var_data_power, __kernel_smc_startpointer_power, __kernel_smc_startpointer_power_2d, col)

                                // 1 unique indexes
                                // [0] r*col+c
#define __ipmacc_smc_index_power_0_dim1 r-__kernel_smc_startpointer_power
#define __ipmacc_smc_index_power_0_dim2 c-__kernel_smc_startpointer_power_2d

                                {


                                    {
                                        for(int iter = 0; iter < innerIter; iter++)
                                        {
                                            compute = false;
                                            if ((r >= 0) && (c >= 0) && (r < row) && (c < col) &&
                                                    __accelerator_INRANGE(rs, cs, iter, innerIter, TILEX, TILEY, BLOCKSIZEX, BLOCKSIZEY)) {

                                                compute = true;
                                                delta = (stepCap) * (__kernel_smc_var_data_power[__ipmacc_smc_index_power_0_dim1][__ipmacc_smc_index_power_0_dim2] /* replacing power [r * col + c]*/  +
                                                        (__kernel_smc_var_data_temp[__ipmacc_smc_index_temp_0_dim1][__ipmacc_smc_index_temp_0_dim2] /* replacing temp [S * col + c]*/  + __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_1_dim1][__ipmacc_smc_index_temp_1_dim2] /* replacing temp [N * col + c]*/  - 2.0 * __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_2_dim1][__ipmacc_smc_index_temp_2_dim2] /* replacing temp [r * col + c]*/ ) * rRy +
                                                        (__kernel_smc_var_data_temp[__ipmacc_smc_index_temp_3_dim1][__ipmacc_smc_index_temp_3_dim2] /* replacing temp [r * col + E]*/  + __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_4_dim1][__ipmacc_smc_index_temp_4_dim2] /* replacing temp [r * col + W]*/  - 2.0 * __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_2_dim1][__ipmacc_smc_index_temp_2_dim2] /* replacing temp [r * col + c]*/ ) * rRx +
                                                        (amb_temp - __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_2_dim1][__ipmacc_smc_index_temp_2_dim2] /* replacing temp [r * col + c]*/ ) * rRz);
                                                new_temp = delta + __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_2_dim1][__ipmacc_smc_index_temp_2_dim2] /* replacing temp [r * col + c]*/ ;
                                            }
                                            if (iter == (innerIter - 1)) {
                                                break;
                                            }
                                            if (compute) {

                                                __syncthreads();
                                                __kernel_smc_var_data_temp[__ipmacc_smc_index_temp_2_dim1][__ipmacc_smc_index_temp_2_dim2]= new_temp;
                                                __syncthreads();
                                            }
                                        }
                                    }
                                }
#undef temp
#undef power

                                //end up with the clause (temp[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0],power[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0])
                            }



                            if (compute) {
                                result [r * col + c] = new_temp;   

                            }
                        }

                    }
                }

            }
        }
    }
}


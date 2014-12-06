#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
using namespace std;
#define STR_SIZE	256

/* maximum power density possible (say 300W for a 10mm x 10mm chip)	*/
#define MAX_PD	(3.0e6)
/* required precision in degrees	*/
#define PRECISION	0.001
#define SPEC_HEAT_SI 1.75e6
#define K_SI 100
/* capacitance fitting factor	*/
#define FACTOR_CHIP	0.5

/* chip parameters	*/
double t_chip = 0.0005;
double chip_height = 0.016;
double chip_width = 0.016;
/* ambient temperature, assuming no package at all	*/
double amb_temp = 80.0;
#define BLOCKSIZEX 16 // change the thread block size in ipmacc/codegen.py accordingly
#define BLOCKSIZEY 16 // change the thread block size in ipmacc/codegen.py accordingly
#define BLOCKSIZEXLOG 4
#define BLOCKSIZEYLOG 4

/* Single iteration of the transient solver in the grid model.
 * advances the solution of the discretized difference equations 
 * by one time step
 */
bool INRANGE(int rid, int cid, int iter, int innerIter, int tiler, int tilec, int blockdimr, int blockdimc)
{
    int localdimr=(blockdimr);
    int localdimc=(blockdimc);
    int localr=rid&(localdimr-1);
    int localc=cid&(localdimc-1);
    return ((localr>iter)&&(localc>iter)) &&
        ((localr<(blockdimr-iter-1))&&(localc<(blockdimc-iter-1)));
}
void single_iteration(double *result, double *temp, double *power, int row, int col,
        double Cap, double Rx, double Ry, double Rz, 
        double step, int innerIter, int *written)
{
    double delta;
    double stepCap=step/Cap;
    double rRx=1/Rx;
    double rRy=1/Ry;
    double rRz=1/Rz;
    int rs, cs;
#define TILEX (BLOCKSIZEX-2*innerIter)
#define TILEY (BLOCKSIZEY-2*innerIter)

    int dimrow=(row+((2*innerIter)*(row/TILEX+1)));
    int dimcol=(col+((2*innerIter)*(col/TILEY+1)));
    //#pragma acc parallel loop present(temp, power, result)
#pragma acc kernels present(temp, power, result, written)
#pragma acc loop independent vector(BLOCKSIZEY)
    for (rs=0; rs<dimrow; rs++) {
        int r=rs-((rs>>BLOCKSIZEXLOG)*2*innerIter+innerIter);
#pragma acc loop independent vector(BLOCKSIZEX)
        for (cs=0; cs<dimcol; cs++) {
            int c=cs-((cs>>BLOCKSIZEYLOG)*2*innerIter+innerIter);
            double new_temp;
            bool compute=false;

            {
                int S=(r==(row-1))?row-1:r+1;
                int N=(r==(0))    ?0:r-1;
                int W=(c==(0))    ?0:c-1;
                int E=(c==(col-1))?col-1:c+1;
#pragma acc cache (temp[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0],power[0:row:0:col:FETCH_CHANNEL:r:0:0:c:0:0:false:0:0:0:0])
                {
                    for(int iter=0; iter<innerIter; iter++){
                        compute=false;
                        if( (r>=0) && (c>=0) && (r<row) && (c<col) &&
                                INRANGE(rs,cs,iter,innerIter,TILEX,TILEY,BLOCKSIZEX,BLOCKSIZEY)){
                            //	Corner 1
                            compute=true;
                            delta = (stepCap) * (power[r*col+c] + 
                                    (temp[S*col+c] + temp[N*col+c] - 2.0*temp[r*col+c]) * rRy + 
                                    (temp[r*col+E] + temp[r*col+W] - 2.0*temp[r*col+c]) * rRx + 
                                    (amb_temp - temp[r*col+c]) * rRz);
                            new_temp= delta + temp[r*col+c];
                        }
                        if(iter==(innerIter-1))
                            break;
                        if(compute){
                            //new_temp = temp[r*col+c]+delta;
                            temp[r*col+c] = new_temp;
                        }
                    }
                }
            }
            /*	Update Temperatures	*/
            //result[r*col+c] =temp[r*col+c]+ delta;
            //__syncthreads();
            if(compute){
                result[r*col+c] = new_temp;//temp[r*col+c];
                //written[r*col+c] = 1;
            }
        }
    }

    //	// #pragma acc parallel loop present(temp, result)
    // int r,c;
    // #pragma acc kernels present(temp, result)
    // #pragma acc loop independent
    // for (r = 0; r < row; r++) {
    // 	#pragma acc loop independent
    // 	for (c = 0; c < col; c++) {
    // 		temp[r*col+c]=result[r*col+c];
    // 	}
    // }
}

/* Transient solver driver routine: simply converts the heat 
 * transfer differential equations to difference equations 
 * and solves the difference equations by iterating
 */
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

#pragma acc data create(result[0:row*col]) \
    copyin(power[0:row*col]) copy(temp[0:row*col],written[0:row*col])
    {
        for (int i = 0; i < num_iterations/inner_iter ; i++)
        {
#ifdef VERBOSE
            fprintf(stdout, "iteration %d\n", i++);
#endif
            single_iteration(result, temp, power, row, col, Cap, Rx, Ry, Rz, step, inner_iter, written);
            double *tmp=temp;
            temp=result;
            result=tmp;
        }
    } /* end pragma acc data */	

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
    char str[STR_SIZE];
    double val;

    fp = fopen (file, "r");
    if (!fp)
        fatal ("file could not be opened for reading");

    for (i=0; i < grid_rows * grid_cols; i++) {
        fgets(str, STR_SIZE, fp);
        if (feof(fp))
            fatal("not enough lines in file");
        if ((sscanf(str, "%lf", &val) != 1) )
            fatal("invalid file format");
        vect[i] = val;
    }

    fclose(fp);	
}

void usage(int argc, char **argv)
{
    fprintf(stderr, "Usage: %s <grid_rows> <grid_cols> <inner_iter> <sim_time> <temp_file> <power_file>\n", argv[0]);
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
    acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
#endif 

    int grid_rows, grid_cols, sim_time, inner_iter;
    double *temp, *power, *result;
    int *written;
    char *tfile, *pfile;

    /* check validity of inputs	*/
    if (argc != 7)
        usage(argc, argv);
    if ((grid_rows = atoi(argv[1])) <= 0 ||
            (grid_cols = atoi(argv[2])) <= 0 ||
            (sim_time = atoi(argv[4])) <= 0 ||
            (inner_iter = atoi(argv[3])) <= 0
       )
        usage(argc, argv);

    /* allocate memory for the temperature and power arrays	*/
    temp = (double *) malloc (grid_rows * grid_cols* sizeof(double));
    power = (double *) malloc (grid_rows * grid_cols* sizeof(double));
    result = (double *) malloc (grid_rows * grid_cols* sizeof(double));
    written = (int *) malloc (grid_rows * grid_cols* sizeof(int));
    if(!temp || !power)
        fatal("unable to allocate memory");

    /* read initial temperatures and input power	*/
    tfile = argv[5];
    pfile = argv[6];
    read_input(temp, grid_rows, grid_cols, tfile);
    read_input(power, grid_rows, grid_cols, pfile);
    int i;
    for(i=0; i<grid_rows * grid_cols; i++){
        written[i]=0;
    }

    printf("Start computing the transient temperature\n");
    compute_tran_temp(result,sim_time, temp, power, grid_rows, grid_cols, inner_iter, written);
    printf("Ending simulation\n");
    /* output results	*/
#ifdef VERBOSE
    fprintf(stdout, "Final Temperatures:\n");
#endif

#ifdef OUTPUT
    //for(i=0; i < grid_rows * grid_cols; i++)
    //	fprintf(stdout, "%d\t[%d]%f\n", i, written[i],temp[i]);
    for(i=0; i < grid_rows * grid_cols; i++)
        fprintf(stdout, "%d\t%f\n", i, temp[i]);
#endif
    /* cleanup	*/
    free(temp);
    free(power);

    return 0;
}


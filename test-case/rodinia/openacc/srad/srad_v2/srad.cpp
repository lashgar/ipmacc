// srad.cpp : Defines the entry point for the console application.
//

//#define OUTPUT


#define OPEN
#define	ITERATION
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

void random_matrix(float *I, int rows, int cols);

void usage(int argc, char **argv)
{
	fprintf(stderr, "Usage: %s <rows> <cols> <y1> <y2> <x1> <x2> <lamda> <no. of iter>\n", argv[0]);
	fprintf(stderr, "\t<rows>   - number of rows\n");
	fprintf(stderr, "\t<cols>    - number of cols\n");
	fprintf(stderr, "\t<y1> 	 - y1 value of the speckle\n");
	fprintf(stderr, "\t<y2>      - y2 value of the speckle\n");
	fprintf(stderr, "\t<x1>       - x1 value of the speckle\n");
	fprintf(stderr, "\t<x2>       - x2 value of the speckle\n");
	fprintf(stderr, "\t<lamda>   - lambda (0,1)\n");
	fprintf(stderr, "\t<no. of iter>   - number of iterations\n");

	exit(1);
}

int main(int argc, char* argv[])
{   
#ifdef __NVCUDA__
	acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
	acc_init( acc_device_nvocl );
	//acc_list_devices_spec( acc_device_nvocl );
#endif 




	int rows, cols, size_I, size_R, niter = 10, iter, k;
	float *I, *J, q0sqr, sum, sum2, tmp, meanROI,varROI ;
	float Jc, G2, L, num, den, qsqr;
	int *iN,*iS,*jE,*jW;
	float *dN,*dS,*dW,*dE;
	int r1, r2, c1, c2;
	float cN,cS,cW,cE;
	float *c, D;
	float lambda;
	int i, j;
	printf("%d \n", argc );

	if (argc ==9 )
	{
		rows = atoi(argv[1]); //number of rows in the domain
		cols = atoi(argv[2]); //number of cols in the domain
		if ((rows%16!=0) || (cols%16!=0)){
			fprintf(stderr, "rows and cols must be multiples of 16\n");
			exit(1);
		}
		r1   = atoi(argv[3]); //y1 position of the speckle
		r2   = atoi(argv[4]); //y2 position of the speckle
		c1   = atoi(argv[5]); //x1 position of the speckle
		c2   = atoi(argv[6]); //x2 position of the speckle
		lambda = atof(argv[7]); //Lambda value
		niter = atoi(argv[8]); //number of iterations
	}
	else{
		usage(argc, argv);
	}


	size_I = cols * rows;
	size_R = (r2-r1+1)*(c2-c1+1);   

	I = (float *)malloc( size_I * sizeof(float) );
	J = (float *)malloc( size_I * sizeof(float) );
	c  = (float *)malloc(sizeof(float)* size_I) ;

	iN = (int *)malloc(sizeof(unsigned int*) * rows) ;
	iS = (int *)malloc(sizeof(unsigned int*) * rows) ;
	jW = (int *)malloc(sizeof(unsigned int*) * cols) ;
	jE = (int *)malloc(sizeof(unsigned int*) * cols) ;    


	dN = (float *)malloc(sizeof(float)* size_I) ;
	dS = (float *)malloc(sizeof(float)* size_I) ;
	dW = (float *)malloc(sizeof(float)* size_I) ;
	dE = (float *)malloc(sizeof(float)* size_I) ;    

#pragma acc kernels create(iN[0:rows], iS[0:rows])
#pragma acc loop independent
	for (int i=0; i< rows; i++) {
		iN[i] = i-1;
		iS[i] = i+1;
		if (i == 0) iN[0] = 0;
		if (i == rows-1) iS[rows-1] = rows-1;
	}
#pragma acc kernels create(jW[0:cols], jE[0:cols])
#pragma acc loop independent
	for (int j=0; j< cols; j++) {
		jW[j] = j-1;
		jE[j] = j+1;
		if (j == 0) jW[0] = 0;
		if (j == cols-1) jE[cols-1] = cols-1;
	}

	printf("Randomizing the input matrix\n");

	random_matrix(I, rows, cols);

#pragma acc kernels copyin(I[0:size_I]) create(J[0:size_I])
#pragma acc loop independent
	for (k = 0;  k < size_I; k++ ) {
		J[k] = (float)exp(I[k]) ;
	}

	printf("Start the SRAD main loop\n");

#pragma acc data copyout(J[0:size_I]) \
	create(dN[0:size_I], dS[0:size_I], dW[0:size_I], dE[0:size_I], c[0:size_I]) \
	present(iN, iS, jW, jE)
	{
#ifdef ITERATION

		for (iter=0; iter< niter; iter++){
#endif        
			sum=0; sum2=0;
#pragma acc kernels     
#pragma acc loop vector reduction(+:sum,+:sum2) independent
			for (i=r1; i<=r2; i++) {
				//    	#pragma acc loop vector reduction(+:sum,+:sum2) independent
				for (j=c1; j<=c2; j++) {
					tmp   = J[i * cols + j];
					sum  += tmp ;
					sum2 += tmp*tmp;
				}
			}
			meanROI = sum / size_R;
			varROI  = (sum2 / size_R) - meanROI*meanROI;
			q0sqr   = varROI / (meanROI*meanROI);


#pragma acc kernels
#pragma acc loop independent
			for (int i = 0 ; i < rows ; i++) {
				for (int j = 0; j < cols; j++) { 

					k = i * cols + j;
					Jc = J[k];

					// directional derivates
					dN[k] = J[iN[i] * cols + j] - Jc;
					dS[k] = J[iS[i] * cols + j] - Jc;
					dW[k] = J[i * cols + jW[j]] - Jc;
					dE[k] = J[i * cols + jE[j]] - Jc;

					G2 = (dN[k]*dN[k] + dS[k]*dS[k] 
							+ dW[k]*dW[k] + dE[k]*dE[k]) / (Jc*Jc);

					L = (dN[k] + dS[k] + dW[k] + dE[k]) / Jc;

					num  = (0.5*G2) - ((1.0/16.0)*(L*L)) ;
					den  = 1 + (.25*L);
					qsqr = num/(den*den);

					// diffusion coefficent (equ 33)
					den = (qsqr-q0sqr) / (q0sqr * (1+q0sqr)) ;
					c[k] = 1.0 / (1.0+den) ;

					// saturate diffusion coefficent
					if (c[k] < 0) {c[k] = 0;}
					else if (c[k] > 1) {c[k] = 1;}

				}
			}

#pragma acc kernels
#pragma acc loop independent
			for (int i = 0; i < rows; i++) {
				for (int j = 0; j < cols; j++) {        

					// current index
					k = i * cols + j;

					// diffusion coefficent
					cN = c[k];
					cS = c[iS[i] * cols + j];
					cW = c[k];
					cE = c[i * cols + jE[j]];

					// divergence (equ 58)
					D = cN * dN[k] + cS * dS[k] + cW * dW[k] + cE * dE[k];

					// image update (equ 61)
					J[k] = J[k] + 0.25*lambda*D;
#ifdef OUTPUT
					//printf("%.5f ", J[k]); 
#endif //output
				}
#ifdef OUTPUT
				//printf("\n"); 
#endif //output
			}

#ifdef ITERATION
		}
#endif

	} /* end pragma acc data */


	//#ifdef OUTPUT
	for( int i = 0 ; i < rows ; i++){
		for ( int j = 0 ; j < cols ; j++){

			printf("%.5f ", J[i * cols + j]); 

		}
		printf("\n"); 
	}
	//#endif 

	printf("Computation Done\n");

	free(I);
	free(J);
	free(iN); free(iS); free(jW); free(jE);
	free(dN); free(dS); free(dW); free(dE);

	free(c);
	return 0;
}




void random_matrix(float *I, int rows, int cols){

	srand(7);

	for( int i = 0 ; i < rows ; i++){
		for ( int j = 0 ; j < cols ; j++){
			I[i * cols + j] = rand()/(float)RAND_MAX ;
#ifdef OUTPUT
			//printf("%g ", I[i * cols + j]); 
#endif 
		}
#ifdef OUTPUT
		//printf("\n"); 
#endif 
	}

}

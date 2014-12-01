
int SIZE=1000;
int main()
{
    int i,j;

    float **a;
    float **b;
    float **c;
    float **seq;
    a=(float**)malloc(SIZE*sizeof(float*));
    b=(float**)malloc(SIZE*sizeof(float*));
    c=(float**)malloc(SIZE*sizeof(float*));
    seq=(float**)malloc(SIZE*sizeof(float*));

    for(i=0; i<SIZE; i++)
    {
        a[i]=(float*)malloc(SIZE*sizeof(float));
        b[i]=(float*)malloc(SIZE*sizeof(float));
        c[i]=(float*)malloc(SIZE*sizeof(float));
        seq[i]=(float*)malloc(SIZE*sizeof(float));
    }


    acc_init( acc_device_nvidia );




    for(i = 0; i < SIZE; ++i)
    {


        for(j = 0; j < SIZE; ++j)
        {

            a[i][j] = (float)i + j;
            b[i][j] = (float)i - j;
            c[i][j] = 0.0f;
        }


    }



    unsigned long long int tic, toc;


    for(int k=0; k<3; k++)
    {

        printf("Calculation on GPU ... ");
        tic = clock();



        {

            __ungenerated_kernel_function_region__0();

        }

        toc = clock();
        printf(" %6.4f ms\n",(toc-tic)/(float)1000);
    }







    printf("Calculation on CPU ... ");
    tic = clock();

    for(i = 0; i < SIZE; ++i)
    {


        for(j = 0; j < SIZE; ++j)
        {

            seq[i][j] = sin(a[i][j]) + cos(b[i][j]) + cos(a[i][j]*b[i][j]);
            if(c[i][j] != seq[i][j]) {
                printf("Error %d %d\n", i,j);
                exit(1);
            }
        }


    }


    toc = clock();
    printf(" %6.4f ms\n",(toc-tic)/(float)1000);

    printf("OpenACC vector add test was successful!\n");

    return 0;
}



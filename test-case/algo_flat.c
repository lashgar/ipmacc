#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <assert.h>

#define datatype float
#define MAXNEIGHBOR 32
// #define boardersizex 1
// #define boardersizey 1
// #define tilesizex (boardersizex*2+1)
// #define tilesizey (boardersizey*2+1)

void sort(datatype *k, unsigned int length){
    unsigned int i, j;
    for(i = 0; i<length; i++){
        for(j = 0; j<(length-1); j++){
            if(k[j]>k[j+1]){
                datatype tmp = k[j];
                k[j] = k[j+1];
                k[j+1] = tmp;
            }
        }
    }
}

void init(datatype *a, unsigned int dim, unsigned int value)
{
    unsigned int i, j;
    for(i = 0; i<dim; i++){
        unsigned int idx = i;
        a[idx] = 1.0 * (idx%value);
    }
}

void print(datatype *a, unsigned int dim, char *name)
{
    printf("%s\n", name);
    unsigned int i, j;
    for(i = 0; i<dim; i++){
        unsigned int idx = i;
        printf("%6.4f ", a[idx]);
    }
    printf("\n");
}

//#define linesize 1
//#define neighbsize (2*linesize+1)

int main(int argc, char *argv[]){
    unsigned int i, j, k;
    //unsigned int imgsizex = 8;
    //unsigned int imgsizey = 8;
    unsigned rowsize = 32;
    int linesize  =1;
    int neighbsize=(2*linesize+1);

    if(argc>=2){
        sscanf(argv[1], "%d", &linesize);
        neighbsize=(2*linesize+1);
    }else{
        printf("usage: %s radius\n", argv[0]);
        exit(-1);
    }
    if(neighbsize>MAXNEIGHBOR){
        printf("invalid radius size: aborting()\nmaximum radius size is %d\n", (MAXNEIGHBOR-1)/2);
        exit(-1);
    }
    printf("tile size> %d linesize> %d\n", neighbsize, linesize);

    datatype* m_img_in  = (datatype*)malloc(sizeof(datatype)*rowsize);
    init(m_img_in,  rowsize, 31 );
    datatype* m_img_out = (datatype*)malloc(sizeof(datatype)*rowsize);
    init(m_img_out, rowsize, 7 );

    //print(m_img_in,  imgsizey, imgsizex, "Input  [before]: ");
    //print(m_img_out, imgsizey, imgsizex, "Output [before]: ");

    //datatype list[MAXNEIGHBOR];
    #pragma acc data copyin(m_img_in[0:(rowsize)]) copyout(m_img_out[0:(rowsize)])
    {
        #pragma acc kernels 
        #pragma acc loop independent vector(4)
        for(i=0; i<rowsize; ++i){
            datatype list[MAXNEIGHBOR];
            unsigned int k = 0;
            for(k=0; k<neighbsize; ++k){
                list[k] = 1<<30;
            }
            /*
            if(!(idx< imgsizex*imgsizey)){
                printf("failed: %d %d %d %d %d\n", idx, j, i, imgsizex, imgsizey);
                exit(-1);
            }
            */
            int jt;
            for(jt = -linesize; jt<=linesize; ++jt){
                if( (i+jt)<rowsize && (i+jt)>=0 ){
                    //printf("updating\n");
                    list[jt+linesize] = m_img_in[i+jt];
                }
            }
            //printf(" LIST at %dx%d:\n", jt, it);
            //print(list, tilesizey, tilesizex, "partial list:");
            #pragma acc algorithm sort(list[0:(neighbsize)])
            //sort(list, neighbsize);
            m_img_out[i] = list[0];
        }
    }

    print(m_img_in,  rowsize, "Input  [after]: ");
    print(m_img_out, rowsize, "Output [after]: ");

    return 0;
}


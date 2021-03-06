#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <assert.h>

#define datatype int
#define boardersizex 1
#define boardersizey 1
#define tilesizex (boardersizex*2+1)
#define tilesizey (boardersizey*2+1)

void find(datatype *k, unsigned int length, datatype value, int& value_idx){
    unsigned int i;
    for(i = 0; i<length; i++){
        if(k[i]==value){
            value_idx = i;
        }
    }
}

void init(datatype *a, unsigned int ydim, unsigned int xdim, unsigned int value)
{
    unsigned int i, j;
    for(i = 0; i<ydim; i++){
        for(j = 0; j<xdim; j++){
            unsigned int idx = i*xdim+j;
            a[idx] = (idx%value);
        }
    }
}

void print(datatype *a, unsigned int ydim, unsigned int xdim, char *name)
{
    printf("%s\n", name);
    unsigned int i, j;
    for(i = 0; i<ydim; i++){
        for(j = 0; j<xdim; j++){
            unsigned int idx = i*xdim+j;
            printf("%6d ", a[idx]);
        }
        printf("\n");
    }
}

void compare(datatype *a, datatype *b, unsigned int ydim, unsigned int xdim)
{
    unsigned int i, j;
    for(i = 0; i<ydim; i++){
        for(j = 0; j<xdim; j++){
            unsigned int idx = i*xdim+j;
            if(a[idx]!=b[idx]){
                printf("[%d][%d] %6d != %6d\n", i, j, a[idx], b[idx]);
                exit(-1);
            }
        }
    }
    printf("test passed!\n");
}

int main(int argc, char *argv[]){
    unsigned int i, j, k;

    unsigned int imgsizex = 0;
    unsigned int imgsizey = 0;
    if(argc!=3){
        printf("usage: %s imgsizex imgsizey\n", argv[0], imgsizex, imgsizey);
        exit(-1);
    }else{
        sscanf(argv[1], "%d", &imgsizex);
        sscanf(argv[2], "%d", &imgsizey);
    }
    assert(imgsizex>0);
    assert(imgsizey>0);
    printf("image size: %dx%d\n", imgsizex, imgsizey);

    datatype* m_img_in  = (datatype*)malloc(sizeof(datatype)*imgsizex*imgsizey);
    init(m_img_in, imgsizey, imgsizex, 31 );
    datatype* m_img_out = (datatype*)malloc(sizeof(datatype)*imgsizex*imgsizey);
    init(m_img_out, imgsizey, imgsizex, 7 );
    datatype* m_img_out_host = (datatype*)malloc(sizeof(datatype)*imgsizex*imgsizey);
    init(m_img_out_host, imgsizey, imgsizex, 7 );

    //print(m_img_in,  imgsizey, imgsizex, "Input  [before]: ");
    //print(m_img_out, imgsizey, imgsizex, "Output [before]: ");

    // ACC
    datatype list[(tilesizey)*(tilesizex)];
    #pragma acc data copyin(m_img_in[0:(imgsizex*imgsizey)]) copyout(m_img_out[0:(imgsizex*imgsizey)])
    {
        #pragma acc kernels 
        #pragma acc loop independent vector(4)
        for(j=0; j<imgsizey; ++j){
            #pragma acc loop independent vector(8)
            for(i=0; i<imgsizex; ++i){
                datatype list[(tilesizey)*(tilesizex)];
                unsigned int k = 0;
                for(k=0; k<(tilesizey*tilesizex); ++k){
                    list[k] = 1<<30;
                }
                unsigned int idx = j*imgsizex + i;
                /*
                if(!(idx< imgsizex*imgsizey)){
                    printf("failed: %d %d %d %d %d\n", idx, j, i, imgsizex, imgsizey);
                    exit(-1);
                }
                */
                int jt, it;
                for(jt = -boardersizey; jt<=(boardersizey); ++jt){
                    for(it = -boardersizex; it<=(boardersizex); ++it){
                        if( (j+jt)<imgsizey && (i+it)<imgsizex &&
                            (j+jt)>=0       && (i+it)>=0 ){
                            //printf("updating\n");
                            list[(jt+boardersizey)*tilesizex+(it+boardersizex)] = m_img_in[(j+jt)*imgsizex+(i+it)];
                        }
                    }
                }
                //printf(" LIST at %dx%d:\n", jt, it);
                //print(list, tilesizey, tilesizex, "partial list:");
                int value_idx = -1;
                datatype value = 12;
                #pragma acc algorithm find(list[0:(tilesizex*tilesizey)],value,value_idx)
                //find(list, tilesizex*tilesizey, value, value_idx);
                m_img_out[idx] = value_idx!=-1?1:0;
            }
        }
    }
    // SERIAL
    {
        for(j=0; j<imgsizey; ++j){
            for(i=0; i<imgsizex; ++i){
                datatype list[(tilesizey)*(tilesizex)];
                unsigned int k = 0;
                for(k=0; k<(tilesizey*tilesizex); ++k){
                    list[k] = 1<<30;
                }
                unsigned int idx = j*imgsizex + i;
                /*
                if(!(idx< imgsizex*imgsizey)){
                    printf("failed: %d %d %d %d %d\n", idx, j, i, imgsizex, imgsizey);
                    exit(-1);
                }
                */
                int jt, it;
                for(jt = -boardersizey; jt<=(boardersizey); ++jt){
                    for(it = -boardersizex; it<=(boardersizex); ++it){
                        if( (j+jt)<imgsizey && (i+it)<imgsizex &&
                            (j+jt)>=0       && (i+it)>=0 ){
                            //printf("updating\n");
                            list[(jt+boardersizey)*tilesizex+(it+boardersizex)] = m_img_in[(j+jt)*imgsizex+(i+it)];
                        }
                    }
                }
                //printf(" LIST at %dx%d:\n", jt, it);
                //print(list, tilesizey, tilesizex, "partial list:");
                //#pragma acc algorithm sort(list[0:(tilesizex*tilesizey)])
                int value_idx = -1;
                datatype value = 12;
                find(list, tilesizex*tilesizey, value, value_idx);
                m_img_out_host[idx] = value_idx!=-1?1:0;
            }
        }
    }

    // print(m_img_in,  imgsizey, imgsizex, "Input  [after]: ");
    // print(m_img_out, imgsizey, imgsizex, "Output [after]: ");
    compare(m_img_out, m_img_out_host, imgsizey, imgsizex);

    int sum_host = 0;
    int sum_dev  = 0;
    for(j=0; j<imgsizey; ++j){
        for(i=0; i<imgsizex; ++i){
            sum_dev  += m_img_out[j*imgsizex+i];
            sum_host += m_img_out_host[j*imgsizex+i];
        }
    }
    printf("boolean sum on host: %d\n", sum_host);
    printf("boolean sum on  dev: %d\n", sum_dev);

    return 0;
}


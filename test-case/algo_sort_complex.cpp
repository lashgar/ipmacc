#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <assert.h>
#include <time.h>


#ifdef __CUDACC__
#define QUALIFIERS __inline__ __device__ __host__
#else
#define QUALIFIERS __inline
#endif

struct pixel_s {
    double intensity;
    double transparency;
    QUALIFIERS bool operator<(const pixel_s &a) const {
        if(intensity<a.intensity){
            return true;
        }else if(intensity>a.intensity){
            return false;
        }else{
            return transparency<a.transparency;
        }
    }
    QUALIFIERS bool operator<=(const pixel_s &a) const {
        if(intensity<a.intensity){
            return true;
        }else if(intensity>a.intensity){
            return false;
        }else{
            return transparency<=a.transparency;
        }
    }
    QUALIFIERS bool operator>(const pixel_s &a) const {
        if(intensity>a.intensity){
            return true;
        }else if(intensity<a.intensity){
            return false;
        }else{
            return transparency>a.transparency;
        }
    }
    QUALIFIERS bool operator>=(const pixel_s &a) const {
        if(intensity>a.intensity){
            return true;
        }else if(intensity<a.intensity){
            return false;
        }else{
            return transparency>=a.transparency;
        }
    }
    QUALIFIERS bool operator==(const pixel_s &a) const{
        return intensity==a.intensity && transparency==a.transparency;
    }
    QUALIFIERS bool operator!=(const pixel_s &a) const{
        return intensity!=a.intensity || transparency!=a.transparency;
    }
    QUALIFIERS const pixel_s& operator=(const pixel_s &a) {
        intensity=a.intensity;
        transparency=a.transparency;
        return (*this);
    }

};

#define datatype pixel_s
#define MAXTILESIZE 1024


void shell_sort (datatype *a, int n) {
    int h, i, j;
    datatype t;
    for (h = n; h /= 2;) {
        for (i = h; i < n; i++) {
            t = a[i];
            for (j = i; j >= h && t < a[j - h]; j -= h) {
                a[j] = a[j - h];
            }
            a[j] = t;
        }
    }
}


void gnome_sort(datatype *a, int n)
{
  int i=1, j=2;
  datatype t;
#define swap(i, j) { t = a[i]; a[i] = a[j]; a[j] = t; } 
  while(i < n) {
    if (a[i - 1] > a[i]) {
      swap(i - 1, i);
      if (--i) continue;
    }
    i = j++;
  }
#undef swap
}
void selection_sort (datatype *a, int n) {
    int i, j, m;
    datatype t;
    for (i = 0; i < n; i++) {
        for (j = i, m = i; j < n; j++) {
            if (a[j] < a[m]) {
                m = j;
            }
        }
        t = a[i];
        a[i] = a[m];
        a[m] = t;
    }
}

void insertion_sort(datatype *a, int n) {
    for(int i = 1; i < n; ++i) {
        datatype tmp = a[i];
        int j = i;
        while(j > 0 && tmp < a[j - 1]) {
            a[j] = a[j - 1];
            --j;
        }
        a[j] = tmp;
    }
}

int max (datatype *a, int n, int i, int j, int k) {
    int m = i;
    if (j < n && a[j] > a[m]) {
        m = j;
    }
    if (k < n && a[k] > a[m]) {
        m = k;
    }
    return m;
}
 
void downheap (datatype *a, int n, int i) {
    while (1) {
        int j = max(a, n, i, 2 * i + 1, 2 * i + 2);
        if (j == i) {
            break;
        }
        datatype t = a[i];
        a[i] = a[j];
        a[j] = t;
        i = j;
    }
}
 
void heap_sort (datatype *a, int n) {
    int i;
    for (i = (n - 2) / 2; i >= 0; i--) {
        downheap(a, n, i);
    }
    for (i = 0; i < n; i++) {
        datatype t = a[n - i - 1];
        a[n - i - 1] = a[0];
        a[0] = t;
        downheap(a, n - i - 1, 0);
    }
}

void quick_sort (datatype *a, int n) {
    int i, j;
    datatype p, t;
    if (n < 2)
        return;
    p = a[n / 2];
    for (i = 0, j = n - 1;; i++, j--) {
        while (a[i] < p)
            i++;
        while (p < a[j])
            j--;
        if (i >= j)
            break;
        t = a[i];
        a[i] = a[j];
        a[j] = t;
    }
    quick_sort(a, i);
    quick_sort(a + i, n - i);
}

void bubble_sort(datatype *k, unsigned int length){
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

void init(datatype *a, unsigned int ydim, unsigned int xdim, unsigned int value)
{
    unsigned int i, j;
    srand(time(NULL));
    for(i = 0; i<ydim; i++){
        for(j = 0; j<xdim; j++){
            unsigned int idx = i*xdim+j;
            a[idx].intensity = 1.0 * (rand());
            a[idx].transparency = 1.0 * (rand());
            //a[idx] = 1.0 * (idx%value);
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
            printf("%6.4f ", a[idx]);
        }
        printf("\n");
    }
}

void compare(datatype *a, datatype *b, unsigned int ydim, unsigned int xdim)
{
    unsigned int i, j;
    unsigned int nmismatch=0;
    for(i = 0; i<ydim; i++){
        for(j = 0; j<xdim; j++){
            unsigned int idx = i*xdim+j;
            if(a[idx]!=b[idx]){
                if(++nmismatch<20){
                    printf("mismatch #%d [%d][%d] %6.4f != %6.4f\n", nmismatch, i, j, a[idx].intensity, b[idx].intensity);
                }
                //exit(-1);
            }
        }
    }
    if(nmismatch==0) printf("test passed!\n");
}

int main(int argc, char *argv[]){
    unsigned int i, j, k;

    int imgsizex = 0;
    int imgsizey = 0;
    int boardersizex = 0;
    int boardersizey = 0;
    unsigned int verify = 0;
    if(argc!=6){
        printf("usage: %s imgsizex imgsizey boardersizex boardersizey verify\n",
            argv[0]);
        exit(-1);
    }else{
        sscanf(argv[1], "%d", &imgsizex);
        sscanf(argv[2], "%d", &imgsizey);
        sscanf(argv[3], "%d", &boardersizex);
        sscanf(argv[4], "%d", &boardersizey);
        sscanf(argv[5], "%d", &verify);
    }
    assert(imgsizex>0);
    assert(imgsizey>0);
    assert(boardersizex>0);
    assert(boardersizey>0);
    assert(verify==1 || verify==0);
    unsigned int tilesizex = (boardersizex*2+1);
    unsigned int tilesizey = (boardersizey*2+1);
    printf("image size: %dx%d\n", imgsizex, imgsizey);
    printf("tile  size: %dx%d\n", tilesizex, tilesizey);
    assert(MAXTILESIZE>(tilesizey*tilesizex));

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
        #pragma acc loop independent vector(16)
        for(j=0; j<imgsizey; ++j){
            #pragma acc loop independent vector(16)
            for(i=0; i<imgsizex; ++i){
                datatype list[MAXTILESIZE];
                unsigned int k = 0;
                for(k=0; k<(tilesizey*tilesizex); ++k){
                    list[k].intensity = (double)(1<<30);
                    list[k].transparency = (double)(1<<30);
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
                //gnome_sort(list, tilesizex*tilesizey);
                //shell_sort(list, tilesizex*tilesizey);
                bubble_sort(list, tilesizex*tilesizey);
                m_img_out[idx] = list[0];
                // m_img_out[idx].intensity = 1; //list[0];
                // m_img_out[idx].transparency = 2; //list[0];
            }
        }
    }
    // SERIAL
    if(verify)
    {
        for(j=0; j<imgsizey; ++j){
            for(i=0; i<imgsizex; ++i){
                datatype list[MAXTILESIZE];
                unsigned int k = 0;
                for(k=0; k<(tilesizey*tilesizex); ++k){
                    list[k].intensity = (double)(1<<30);
                    list[k].transparency = (double)(1<<30);
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
                quick_sort(list, tilesizex*tilesizey);
                //shell_sort(list, tilesizex*tilesizey);
                //bubble_sort(list, tilesizex*tilesizey);
                m_img_out_host[idx] = list[0];
            }
        }
        // print(m_img_in,  imgsizey, imgsizex, "Input  [after]: ");
        // print(m_img_out, imgsizey, imgsizex, "Output [after]: ");
        compare(m_img_out, m_img_out_host, imgsizey, imgsizex);
    }

    return 0;
}


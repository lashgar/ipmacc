/* This is a very simple program to create the mandelbrot set */

#include <stdio.h>
#include <fcntl.h>
#include <math.h>
#include <stdlib.h>
#include <malloc.h>
#include <iostream>

#ifdef __NVCUDA__ || __NVOPENCL__
#include <openacc.h>
#endif

#define width 640
#define height 480

//#define char int8

int main()
{
    double x,y;
    double xstart,xstep,ystart,ystep;
    double xend, yend;
    double z,zi,newz,newzi;
    double colour;
    int iter=10;
    long col;
    char *pic;//[height][width][3];
    int i,j,k;
    int inset;
    int fd;
    char buffer[100];

#ifdef __NVCUDA__
    acc_init( acc_device_nvcuda );
#endif 
#ifdef __NVOPENCL__
    acc_init( acc_device_nvocl );
    //acc_list_devices_spec( acc_device_nvocl );
#endif 


    pic=(char*)malloc(sizeof(char)*height*width*3);
    /* Read in the initial data */
    xstart=-2;
    xend=1;
    ystart=-1;
    yend=1;

    /* these are used for calculating the points corresponding to the pixels */
    xstep = (xend-xstart)/width;
    ystep = (yend-ystart)/height;

    /*the main loop */
    x = xstart;
    y = ystart;
#pragma acc kernels copy(pic[0:height*width*3])
    {
#pragma acc loop independent private(x,y)
        for (i=0; i<height; i++)
        {
            //        printf("Now on line: %d\n", i);
            y = i*ystep + ystart;
#pragma acc loop independent private(newz,newzi,k,inset,z,zi,colour)
            for (j=0; j<width; j++)
            {
                //,newzi,z,zi,inset)
                z = 0;
                zi = 0;
                inset = 1;
                x=j*xstep + xstart;
                for (k=0; k<iter; k++)
                {
                    // z^2 = (a+bi)(a+bi) = a^2 + 2abi - b^2 
                    newz = (z*z)-(zi*zi) + x;
                    newzi = 2*z*zi + y;
                    z = newz;
                    zi = newzi;
                    if(((z*z)+(zi*zi)) > 4)
                    {
                        inset = 0;
                        colour = k;
                        k = iter;
                    }
                }
                int base=(i*width*3)+ (j*3);
                /*
                pic[base+0]=y;
                pic[base+1]=x;
                pic[base+2]=x+y;
                */
                if (inset)
                {
                    pic[base+0] = 0;
                    pic[base+1] = 0;
                    pic[base+2] = 0;
                }
                else
                {
                    pic[base+0] = colour / iter * 255;
                    pic[base+1] = colour / iter * 255 / 2;
                    pic[base+2] = colour / iter * 255 / 2;
                }
                //            x += xstep;
            }
            //        y += ystep;
            //        x = xstart;
        }
    }

    /* writes the data to a TGA file */
    if ((fd = open("mand.tga", O_RDWR+O_CREAT, 0)) == -1)
    {
        fprintf(stderr,"error opening file\n");
        exit(1);
    }
    printf("mandelbrot computation done!\n");
    buffer[0] = 0;
    buffer[1] = 0;
    buffer[2] = 2;
    buffer[8] = 0; buffer[9] = 0;
    buffer[10] = 0; buffer[11] = 0;
    buffer[12] = (width & 0x00FF); buffer[13] = (width & 0xFF00) >> 8;
    buffer[14] = (height & 0x00FF); buffer[15] = (height & 0xFF00) >> 8;
    buffer[16] = 24;
    buffer[17] = 0;
    write(fd, buffer, 18);
    write(fd, pic, width*height*3);
    close(fd);
}


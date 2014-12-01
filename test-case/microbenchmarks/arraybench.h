/***************************************************************************
 *                                                                         *
 *             OpenMP MicroBenchmark Suite - Version 2.0                   *
 *                                                                         *
 *                            produced by                                  *
 *                                                                         *
 *                     Mark Bull and Fiona Reid                            *
 *                                                                         *
 *                                at                                       *
 *                                                                         *
 *                Edinburgh Parallel Computing Centre                      *
 *                                                                         *
 *         email: markb@epcc.ed.ac.uk or fiona@epcc.ed.ac.uk               *
 *                                                                         *
 *                                                                         *
 *      This version copyright (c) The University of Edinburgh, 2004.      *
 *                         All rights reserved.                            *
 *                                                                         *
 **************************************************************************/

#define OUTERREPS 40 
#define CONF95 1.96 




void refer(); 
/*
   void testfirstprivnew(); 

   void testprivnew();

   void testcopyprivnew();   */
void copyintest();
void copyouttest();
void createtest();
void reductiontest();   
void privatetest();
void kerneltest();

double getclock(void); 
void delay(int, double*);

void stats(double*, double*, double*); 



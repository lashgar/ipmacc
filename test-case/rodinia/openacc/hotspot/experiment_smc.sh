#!/bin/bash

ROOT=$IPMACCROOT/test-case/rodinia/
# CONFIG
COMPILE=0
VERIFY=0 # print the running command of CUDA and OpenACC for each benchmark
RUN=1
ITER=30
DEBUG=0

function run_benchmarks_nvprof()
{
 path=$1 # root path to benchmarks directory. e.g. $ROOT/cude
 iter=$2 # number of iterations
 tp=$3 #cuda or openacc
 i=$4 #benchmark name
 args="$5 $6 "
 GPU="Tesla K20c"
 #echo "$path <for $iter times>"
 #echo 'benchmark,hmean,min,max'
 #for i in nbody;
 #for i in backprop bfs fastWalshTransform hotspot nbody nn nw pathfinder srad;
 #do
  cd $path/$i
  if [ "$DEBUG" == "1" ] ; then
   echo "=======DEBUGGING $i========"
   #cp $path/$i/runnvprof $path/$i/runnvprof_api
   #vim $path/$i/runnvprof_api
   #bash $path/$i/runnvprof
   nvprof --print-gpu-trace ./hotspot_ipmacc_cuda 1024 1024 $args  ../../data/hotspot/temp_1024 ../../data/hotspot/power_1024 &> ../../$i.$3.txt
  else
   kernel=
   memory=
   launch=
   for (( j=0; j<$iter; j++)); do
    #nvprof --print-gpu-trace ./pathfinder_cache $args &> .log.txt
    nvprof --print-gpu-trace ./hotspot_ipmacc_cuda 1024 1024 $args  ../../data/hotspot/temp_1024 ../../data/hotspot/power_1024 &> .log.txt 
    #bash $path/$i/runnvprof &> .log.txt
    #nvprof --print-api-summary ./pathfinder_cache $args &> .log_api.txt
    nvprof --print-api-summary ./hotspot_ipmacc_cuda 1024 1024 $args  ../../data/hotspot/temp_1024 ../../data/hotspot/power_1024 &> .log_api.txt 
    #bash $path/$i/runnvprof_api &> .log_api.txt
    #cat .log.txt
    #nvprof --print-gpu-trace ... &> .log.txt
    allt=`cat .log.txt | grep "$GPU" | awk '{print $2}'`
    d2ht=`cat .log.txt | grep "CUDA memcpy DtoH" | awk '{print $2}'`
    h2dt=`cat .log.txt | grep "CUDA memcpy HtoD" | awk '{print $2}'`
    apis=`cat .log_api.txt | grep -e cudaLaunch -e cudaSetupArgument -e cudaConfigureCall | awk '{print $2}'`
    #echo $allt $d2ht $h2dt
    all=`echo $allt | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    d2h="0+"`echo $d2ht | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    h2d="0+"`echo $h2dt | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    apis="0+"`echo $apis | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    all=`echo $all | bc`
    d2h=`echo $d2h | bc`
    h2d=`echo $h2d | bc`
    apis=`echo $apis | bc`
    kernel=`echo $all-$d2h-$h2d | bc`,$kernel
    memory=`echo $d2h+$h2d | bc`,$memory
    launch=`echo $apis | bc`,$launch
    rm .log.txt .log_api.txt
   done
   # calculate hmean, max, min
   echo 'from scipy import stats' > .hmean.py
   echo "a=$kernel" >> .hmean.py
   echo "b=$memory" >> .hmean.py
   echo "c=$launch" >> .hmean.py
   #echo "print '$i,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))" >> .hmean.py
   #echo "print '$i,memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b))" >> .hmean.py
   echo "print '${i},$tp,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))+',memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b))+',launch,'+str(stats.hmean(c))+','+str(min(c))+','+str(max(c))" >> .hmean.py
   #echo "print '$i,$tp,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))+',memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b))" >> .hmean.py
   python .hmean.py
   rm .hmean.py
  fi
 #done
}

if [ "$RUN" == "1" ]; then
 echo 'benchmark,backend,kernel,hmean,min,max,memory,hmean,min,max'
 run_benchmarks_nvprof $ROOT/openacc/ $ITER smc_1  hotspot 1
 run_benchmarks_nvprof $ROOT/openacc/ $ITER smc_2  hotspot 2
 run_benchmarks_nvprof $ROOT/openacc/ $ITER smc_4  hotspot 4
 run_benchmarks_nvprof $ROOT/openacc/ $ITER smc_8  hotspot 8
 run_benchmarks_nvprof $ROOT/openacc/ $ITER smc_16 hotspot 16
fi

#run OpenACC-over-CUDA

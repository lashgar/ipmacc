#!/bin/bash

ROOT=$IPMACCROOT/test-case/rodinia/
# CONFIG
COMPILE=1
VERIFY=1 # print the running command of CUDA and OpenACC for each benchmark
RUN=1
ITER=3
DEBUG=0

###########
# COMPILE #
###########
#compile CUDA native
if [ "$COMPILE" == "1" ]; then
 for i in backprop bfs hotspot nn nw pathfinder srad nbody; do
  echo "=====compiling $i====="
  #vim $ROOT/cuda/$i/Makefile
  make -B -C $ROOT/cuda/$i > /dev/null
  sleep 1
 done
fi
#compile OpenACC-over-CUDA
if [ "$COMPILE" == "1" ]; then
 for i in backprop bfs hotspot nn nw pathfinder srad nbody; do
  echo "=====compiling $i====="
  #vim $ROOT/openacc/$i/Makefile
  make -B -C $ROOT/openacc/$i cuda > /dev/null
  sleep 1
 done
fi

##########
# VERIFY #
##########
#verify CUDA
if [ "$VERIFY" == "1" ]; then
 for i in backprop bfs hotspot nn nw pathfinder srad nbody;
 do
  echo "=====running arguments of $i under CUDA====="
  cat $ROOT/cuda/$i/runnvprof
  #cp $ROOT/cuda/$i/run $ROOT/cuda/$i/runnvprof
  #vim $ROOT/cuda/$i/runnvprof
  echo "=====running arguments of $i under OpenACC====="
  cat $ROOT/openacc/$i/runnvprof
  #cp $ROOT/openacc/$i/run $ROOT/openacc/$i/runnvprof
  #vim $ROOT/openacc/$i/runnvprof
  #vim $ROOT/openacc/$i/run
  sleep 1
 done
fi

#######
# RUN #
#######

#run the binary, measure based on the Linux time
function run_benchmarks_time()
{
 path=$1 # root path to benchmarks directory. e.g. $ROOT/cude
 iter=$2 # number of iterations
 echo "$path <for $iter times>"
 echo 'benchmark,hmean,min,max'
 for i in backprop bfs hotspot nn nw pathfinder srad nbody;
 do
  #echo "=====running $i====="
  #cd $ROOT/cuda/$i/
  cd $path/$i
  #cat $ROOT/cuda/$i/run
  # stat
  if [ "$DEBUG" == "1" ] ; then
   echo "=======DEBUGGING $i========"
   bash $path/$i/run
  else
   num=
   for (( j=0; j<$iter; j++)); do
    bash -c $path/$i/run &> .tmp
    #bash -c $ROOT/cuda/$i/run &> .tmp
    #bash $ROOT/cuda/$i/run
    num=`cat .tmp | tail -n 3 | grep real | awk '{print $2}' | sed 's/m/\*60\+/g' | sed 's/s//g' | bc`,$num
    rm .tmp
   done
   # calculate hmean, max, min
   echo 'from scipy import stats' > .hmean.py
   echo "a=$num" >> .hmean.py
   echo "print '$i,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))" >> .hmean.py
   python .hmean.py
   rm .hmean.py
  fi
 done
}
# run benchmarks, measure memory transfers and kernel launches
function run_benchmarks_nvprof()
{
 path=$1 # root path to benchmarks directory. e.g. $ROOT/cude
 iter=$2 # number of iterations
 tp=$3 #cuda or openacc
 i=$4 #benchmark name
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
   bash $path/$i/runnvprof &> ../../$i.$3.txt
  else
   kernel=
   memory=
   launch=
   for (( j=0; j<$iter; j++)); do
    bash $path/$i/runnvprof &> .log.txt
    #cat .log.txt
    bash $path/$i/runnvprof_api &> .log_api.txt
    #cat .log.txt
    #nvprof --print-gpu-trace ... &> .log.txt
    allt=`cat .log.txt | grep "$GPU" | awk '{print $2}'`
    d2ht=`cat .log.txt | grep "CUDA memcpy DtoH" | awk '{print $2}'`
    h2dt=`cat .log.txt | grep "CUDA memcpy HtoD" | awk '{print $2}'`
    apis=`cat .log_api.txt | grep -e cudaLaunch -e cudaSetupArgument -e cudaConfigureCall | awk '{print $2}'`
    #echo $allt $d2ht $h2dt $apis
    all=`echo $allt | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    d2h="0+"`echo $d2ht | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    h2d="0+"`echo $h2dt | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    apis="0+"`echo $apis | sed 's/ns//g' | sed 's/us/\*1000/g' | sed 's/ms/\*1000000/g' | sed 's/s/\*1000000000/g' | sed 's/\ /\+/g'`
    #echo $all $d2h $h2d $apis
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
   echo "print '$i,$tp,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))+',memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b))+',launch,'+str(stats.hmean(c))+','+str(min(c))+','+str(max(c))" >> .hmean.py
   #echo "print '$i,$tp,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))+',memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b))" >> .hmean.py
   python .hmean.py
   rm .hmean.py
  fi
 #done
}

if [ "$RUN" == "1" ]; then
 echo 'benchmark,backend,kernel,hmean,min,max,memory,hmean,min,max'
 #for i in fastWalshTransform;
 #for i in hotspot
 for i in backprop bfs hotspot nbody nw pathfinder srad;
 #for i in backprop bfs fastWalshTransform nbody nn nw pathfinder srad;
 #for i in backprop bfs fastWalshTransform hotspot nbody nn nw pathfinder srad;
 do
   run_benchmarks_nvprof $ROOT/openacc/ $ITER openacc $i
   run_benchmarks_nvprof $ROOT/cuda/    $ITER cuda    $i
 done
fi

#run OpenACC-over-CUDA

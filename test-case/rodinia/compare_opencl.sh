#!/bin/bash
# Disclaimer:
# COMPILE AND VERIFY routines can be used under any platforms.
# RUN script is only compatible with NVIDIA environment profiling COMPUTE_PROFILE

ROOT=$IPMACCROOT/test-case/rodinia/
# CONFIG
COMPILE=1 # compile openacc-over-opencl and OpenCL versions (1) or not (0)
VERIFY=1 # print the running command of CUDA and OpenACC for each benchmark
RUN=1  # whether to run (1) or not (0)
ITER=3 #number of iterations to run each benchmark
DEBUG=0 #1 enable/ 0 disable


# DO NOT MODIFY FOLLOWING LINES!

###########
# COMPILE #
###########
#compile CUDA native
if [ "$COMPILE" == "1" ] ; then
 for i in bfs backprop hotspot nbody nn nw pathfinder srad 
 do
  echo "=====compiling $i====="
  #vim $ROOT/opencl/$i/Makefile
  make -B -C $ROOT/opencl/$i
  sleep 1
#compile OpenACC-over-OpenCL
  echo "=====compiling $i====="
  #vim $ROOT/openacc/$i/Makefile
  make -B -C $ROOT/openacc/$i opencl
  sleep 1
 done
fi

##########
# VERIFY #
##########
#verify CUDA
if [ "$VERIFY" == "1" ]; then
 for i in bfs backprop hotspot nbody nn nw pathfinder srad 
 do
  echo "=====running arguments of $i under OpenCL====="
  cat $ROOT/opencl/$i/run
  #cp $ROOT/cuda/$i/run $ROOT/cuda/$i/runnvprof
  #vim $ROOT/cuda/$i/runnvprof
  echo "=====running arguments of $i under OpenACC====="
  cat $ROOT/openacc/$i/runopencl
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
function run_benchmarks_opencl()
{
 path=$1 # root path to benchmarks directory. e.g. $ROOT/opencl
 iter=$2 # number of iterations
 tp=$3 #opencl or openacc
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
   #launch=
   export COMPUTE_PROFILE=1
   for (( j=0; j<$iter; j++)); do
    bash $path/$i/runopencl &> .log.txt
    #cat .log.txt
    if [ "$tp" == "openacc" ] ; then
        # we initialize all devices, get the last one: 
        fname=opencl_profile_2.log
    else 
        # rodinia initializes the first gpu only , get the first one
        fname=opencl_profile_0.log
    fi
    tot_lines=`cat $fname | grep -c "\n"`
    nline=`expr $tot_lines - 1`
    tmp=`tail -n $tot_lines $fname | grep -v -e memcpyDtoHasync -e memcpyHtoDasync | awk '{print $5}'`
    kernel=`echo $tmp | sed 's/\ /\+/g' | bc`,$kernel
    tmp=`tail -n $tot_lines $fname | grep -e memcpyDtoHasync -e memcpyHtoDasync | awk '{print $5}'`
    memory=`echo $tmp | sed 's/\ /\+/g' | bc`,$memory
    rm .log.txt -f 
   done
   rm opencl_profile_* -f #.log_api.txt
   # calculate hmean, max, min
   echo 'from scipy import stats' > .hmean.py
   echo "a=$kernel" >> .hmean.py
   echo "b=$memory" >> .hmean.py
   #echo "c=$launch" >> .hmean.py
   echo "print '$i,$tp,kernel,'+str(stats.hmean(a))+','+str(min(a))+','+str(max(a))+',memory,'+str(stats.hmean(b))+','+str(min(b))+','+str(max(b)) #+',launch,'+str(stats.hmean(c))+','+str(min(c))+','+str(max(c))" >> .hmean.py
   python .hmean.py
   rm .hmean.py
  fi
 #done
}

if [ "$RUN" == "1" ]; then
 echo 'benchmark,backend,kernel,hmean,min,max,memory,hmean,min,max'
 #for i in fastWalshTransform;
 #for i in bfs
 for i in backprop bfs hotspot nbody nw pathfinder srad;
 #for i in backprop bfs fastWalshTransform nbody nn nw pathfinder srad;
 #for i in backprop bfs fastWalshTransform hotspot nbody nn nw pathfinder srad;
 do
   run_benchmarks_opencl $ROOT/openacc/ $ITER openacc $i
   run_benchmarks_opencl $ROOT/opencl/ $ITER opencl $i
   #run_benchmarks_nvprof $ROOT/openacc/ $ITER openacc $i
 done
fi

#run OpenACC-over-CUDA

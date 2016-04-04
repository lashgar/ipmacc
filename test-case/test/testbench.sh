
rm *_ipmacc* -f
testvector=`ls *.c`
nvector=`echo $testvector | wc -w`
ntotaltest=`expr 3 \* $nvector`
count=1

for file in $testvector
do
    #for platform in intelispc nvcuda nvopencl 
    for platform in nvopencl nvcuda intelispc
    do
        echo "[ $count of $ntotaltest ] $platform $file"
        count=`expr $count + 1`
        if [[ "$platform" == "intelispc" || "$platform" == "nvopencl" ]] && [[ "$file" == "compression.c" ]] ;
          then
            echo 'skipping compression.c test on ISPC and OpenCL (not implemented)'
            continue
        fi
        ta=$platform ipmacc $file &> /dev/null
        if [ "$?" != "0" ]; then
            echo "compiling $file test failed on $platform"
            continue
            echo "aborting()"
            exit -1
        fi
        ./a.out &> /dev/null
        if [ "$?" != "0" ]; then
            echo "running $file test failed on $platform"
            #echo "aborting()"
            #exit -1
        fi
    done
done

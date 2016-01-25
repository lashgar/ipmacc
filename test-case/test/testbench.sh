
rm *_ipmacc* -f
testvector=`ls *.c`
nvector=`echo $testvector | wc -w`
ntotaltest=`expr 3 \* $nvector`
count=1
for file in $testvector
do
    for platform in intelispc nvcuda nvopencl 
    do
        echo "[ $count of $ntotaltest ] $platform $file"
        ta=$platform ipmacc $file &> /dev/null
        if [ "$?" != "0" ]; then
            echo "compiling $file test failed on $platform"
            echo "aborting()"
            exit -1
        fi
        ./a.out &> /dev/null
        if [ "$?" != "0" ]; then
            echo "running $file test failed on $platform"
            echo "aborting()"
            exit -1
        fi
        count=`expr $count + 1`
    done
done

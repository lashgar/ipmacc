

/* DISCLAIMER: THIS CODE IS INCLUDED FROM CUDA SDK AND MODIFIED A BIT
 * TO BE USED IN THIS PROJECT
 */

//#define DATATYPE DiffIndicatorCompressed
//#define DATATYPE float

//static inline __device__ uint compareFunction1(const DATATYPE &right, const DATATYPE &left)
template<class DATATYPE>
static inline __device__ uint compareFunction1(const DATATYPE &left, const DATATYPE &right)
{
    //if(__isnan(left.diffIndicator1)){
    //    return false;
    //}else if(__isnan(right.diffIndicator1)){
    //    return true;
    //}else{
    //    return (left.diffIndicator1<right.diffIndicator1);
    //}
    if(left<right){
        return true;
    }else{
        return false;
    }
}
//static inline __device__ uint compareFunction2(const DATATYPE &right, const DATATYPE &left)
template<class DATATYPE>
static inline __device__ uint compareFunction2(const DATATYPE &left, const DATATYPE &right)
{
    //if(__isnan(left.diffIndicator1)){
    //    return false;
    //}else if(__isnan(right.diffIndicator1)){
    //    return true;
    //}else{
    //    return (left.diffIndicator1<=right.diffIndicator1);
    //}
    if(left<=right){
        return true;
    }else{
        return false;
    }
}


template<class DATATYPE>
inline __device__ uint binarySearchExclusive(DATATYPE val, DATATYPE *data, uint L, uint stride)
{
    if (L == 0)
    {
        return 0;
    }

    uint pos = 0;

    for (; stride > 0; stride >>= 1)
    {
        uint newPos = umin(pos + stride, L);

        if (compareFunction1<DATATYPE>(data[newPos-1],val))
        //if ((sortDir && (data[newPos - 1] < val)) || (!sortDir && (data[newPos - 1] > val)))
        {
            pos = newPos;
        }
    }

    return pos;
}

template<class DATATYPE>
inline __device__ uint binarySearchInclusive(DATATYPE val, DATATYPE *data, uint L, uint stride)
{
    if (L == 0)
    {
        return 0;
    }

    uint pos = 0;

    for (; stride > 0; stride >>= 1)
    {
        uint newPos = umin(pos + stride, L);

        if (compareFunction2<DATATYPE>(data[newPos-1],val))
        //if ((sortDir && (data[newPos - 1] <= val)) || (!sortDir && (data[newPos - 1] >= val)))
        {
            pos = newPos;
        }
    }

    return pos;
}

//template<class DATATYPE, class sort_dir>
//#define DATATYPE float
template<class DATATYPE>
__device__ void mergeSortSharedCall(
    DATATYPE *s_key,
    //DATATYPE *s_val,
    uint arrayLength,
    uint (*compare1)(const DATATYPE &, const DATATYPE &),
    uint (*compare2)(const DATATYPE &, const DATATYPE &)
)
{
    for (uint stride = 1; stride < arrayLength; stride <<= 1)
    {
        uint     lPos = threadIdx.x & (stride - 1);
        DATATYPE *baseKey = s_key + 2 * (threadIdx.x - lPos);
        //DATATYPE *baseVal = s_val + 2 * (threadIdx.x - lPos);

        __syncthreads();
        DATATYPE keyA = baseKey[lPos +      0];
        DATATYPE keyB = baseKey[lPos + stride];
        //DATATYPE valA = baseVal[lPos +      0];
        //DATATYPE valB = baseVal[lPos + stride];
        uint posA = binarySearchExclusive<DATATYPE>(keyA, baseKey + stride, stride, stride) + lPos;
        uint posB = binarySearchInclusive<DATATYPE>(keyB, baseKey +      0, stride, stride) + lPos;

        __syncthreads();
        baseKey[posA] = keyA;
        baseKey[posB] = keyB;
        //baseVal[posA] = valA;
        //baseVal[posB] = valB;
    }

    __syncthreads();
}


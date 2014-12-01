typedef float cmplx[2];
typedef struct{ float r,i; }cmplx2;
typedef double dcmplx[2];
typedef struct{ double r,i; }dcmplx2;

/* pi/180 */
#define DEG_TO_RADF 0.0174532925199432957692f
#define DEG_TO_RADD 0.0174532925199432957692
/* 180/pi */
#define RAD_TO_DEGF 57.2957795130823208769f
#define RAD_TO_DEGD 57.2957795130823208769

#define CNVRTDEGF(degrees) ((degrees) * DEG_TO_RADF)
#define CNVRTRADF(radians) ((radians) * RAD_TO_DEGF)

#define CNVRTDEGD(degrees) ((degrees) * DEG_TO_RADD)
#define CNVRTRADD(radians) ((radians) * RAD_TO_DEGD)



struct Ebound{ unsigned int e0; int e1,e2,e3,e4,e5,e6,e7,e8,e9; };

__device__ static inline int
__pgi_boundcheck( int value, int lb, int extent, int linenum, int ssnum, int n1, int n2, int n3, int ref, struct Ebound* E )
{
#ifndef CUDA_NO_SM_11_ATOMIC_INTRINSICS
  if( value < lb || value-lb >= extent ){
    if( atomicAdd( &(E->e0), 1 ) == 0 ){
      E->e1 = linenum;
      E->e2 = lb;
      E->e3 = extent+lb-1;
      E->e4 = ssnum;
      E->e5 = value;
      E->e6 = ref;
      E->e7 = n1;
      E->e8 = n2;
      E->e9 = n3;
    }
  }
#endif
  return value;
}

__device__ static inline int
__pgi_imax( int a, int b ) { return max(a,b); }

__device__ static inline int
__pgi_imin( int a, int b ) { return min(a,b); }

__device__ static inline int
__pgi_nint( float a ) { return (int)(a + ((a >= 0.0f) ? 0.5f : -0.5f)); }

__device__ static inline long long
__pgi_llnint( float a ) { return (long long)(a + ((a >= 0.0f) ? 0.5f : -0.5f)); }

__device__ static inline int
#ifdef __PGI_M32
__pgi_ishft( int a, int m )
#else
__pgi_ishft( int m, int a )
#endif
{ return (int)((m>=32)?a:((m<=-32)?a:((m>=0)?(a<<m):(a>>(-m))))); }

__device__ static inline long long
__pgi_kishft( long long a, int m ) { return (long long)(m>=64?a:(m<=-64?a:(m>=0?(a<<m):(a>>(-m))))); }

__device__ static inline int
__pgi_ishftc( int val, int sc, int rc ) /* value, shift count, rightmost bit count */
{
    unsigned int mask = 0xffffffff, field, tmp1, tmp2;
    int n;
    if( rc <= 0 )
	return val;
    mask >>= 32-rc;
    field = val & mask;
    if( sc >= 0 ){
	for( n=sc; n>=rc; n-=rc) ;	/* remainder without % operation */
	if( n == 0 ) return val;
	tmp1 = field << n;
	tmp2 = field >> (rc-n);
    }else{
	for( n=-sc; n>=rc; n-=rc) ;
	if( n == 0 ) return val;
	tmp1 = field >> n;
	tmp2 = field << (rc-n);
    }
    return (val^field) | ((tmp1 | tmp2) & mask);
}

__device__ static inline long long
__pgi_kishftc( long long val, int sc, int rc ) /* value, shift count, rightmost bit count */
{
    unsigned long long mask = 0xffffffffffffffff, field, tmp1, tmp2;
    int n;
    if( rc <= 0 )
	return val;
    mask >>= 64-rc;
    field = val & mask;
    if( sc >= 0 ){
	for( n=sc; n>=rc; n-=rc) ;
	if( n == 0 ) return val;
	tmp1 = field << n;
	tmp2 = field >> (rc-n);
    }else{
	for( n=-sc; n>=rc; n-=rc) ;
	if( n == 0 ) return val;
	tmp1 = field >> n;
	tmp2 = field << (rc-n);
    }
    return (val^field) | ((tmp1 | tmp2) & mask);
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ void
__pgi_cddiv( signed char* res, double real1, double imag1, double real2, double imag2 )
{
    double x, y, r, d, r_mag, i_mag;
    r_mag = real2;
    if( r_mag < 0 ) r_mag = -r_mag;
    i_mag = imag2;
    if( i_mag < 0 ) i_mag = -i_mag;
    if( r_mag <= i_mag ){
	r = real2 / imag2;
	d = 1.0 / (imag2 * (1.0 + r * r));
	x = (real1 * r + imag1) * d;
	y = (imag1 * r - real1) * d;
    }else{
	r = imag2 / real2;
	d = 1.0 / (real2 * (1.0 + r * r));
	x = (real1 + imag1 * r) * d;
	y = (imag1 - real1 * r) * d;
    }
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cddivd( signed char* res, double real1, double imag1, double d )
{
    double x, y;
    x = real1 / d;
    y = imag1 / d;
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cdpowi( signed char* res, double real, double imag, int i )
{
    int k;
    double fr, fi, gr, gi, tr, ti;
    fr = 1.0;
    fi = 0.0;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cddiv( res, 1.0, 0.0, fr, fi );
    }else{
	((double*)res)[0] = fr;
	((double*)res)[1] = fi;
    }
}

__device__ static __inline__ void
__pgi_cdpowk( signed char* res, double real, double imag, long long i )
{
    long long k;
    double fr, fi, gr, gi, tr, ti;
    fr = 1.0;
    fi = 0.0;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned long long)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cddiv( res, 1.0, 0.0, fr, fi );
    }else{
	((double*)res)[0] = fr;
	((double*)res)[1] = fi;
    }
}

__device__ static __inline__ void
__pgi_zcddiv( double real1, double imag1, double real2, double imag2, signed char* res )
{
    double x, y, r, d, r_mag, i_mag;
    r_mag = real2;
    if( r_mag < 0 ) r_mag = -r_mag;
    i_mag = imag2;
    if( i_mag < 0 ) i_mag = -i_mag;
    if( r_mag <= i_mag ){
	r = real2 / imag2;
	d = 1.0 / (imag2 * (1.0 + r * r));
	x = (real1 * r + imag1) * d;
	y = (imag1 * r - real1) * d;
    }else{
	r = imag2 / real2;
	d = 1.0 / (real2 * (1.0 + r * r));
	x = (real1 + imag1 * r) * d;
	y = (imag1 - real1 * r) * d;
    }
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_zcddivd( double real1, double imag1, double d, signed char* res )
{
    double x, y;
    x = real1 / d;
    y = imag1 / d;
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_zcdpowi( double real, double imag, int i, signed char* res )
{
    int k;
    double fr, fi, gr, gi, tr, ti;
    fr = 1.0;
    fi = 0.0;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cddiv( res, 1.0, 0.0, fr, fi );
    }else{
	((double*)res)[0] = fr;
	((double*)res)[1] = fi;
    }
}

__device__ static __inline__ void
__pgi_zcdpowk( double real, double imag, long long i, signed char* res )
{
    long long k;
    double fr, fi, gr, gi, tr, ti;
    fr = 1.0;
    fi = 0.0;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned long long)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cddiv( res, 1.0, 0.0, fr, fi );
    }else{
	((double*)res)[0] = fr;
	((double*)res)[1] = fi;
    }
}

__device__ static inline int
__pgi_dnint( double a ) { return (int)(a + ((a >= 0.0) ? 0.5 : -0.5)); }

__device__ static inline long long
__pgi_lldnint( double a ) { return (long long)(a + ((a >= 0.0) ? 0.5 : -0.5)); }

#endif

__device__ static __inline__ void
__pgi_cdiv( signed char* res, float real1, float imag1, float real2, float imag2 )
{
    float x, y, r, d, r_mag, i_mag;
    r_mag = real2;
    if( r_mag < 0 ) r_mag = -r_mag;
    i_mag = imag2;
    if( i_mag < 0 ) i_mag = -i_mag;
    if( r_mag <= i_mag ){
	r = real2 / imag2;
	d = 1.0f / (imag2 * (1.0f + r * r));
	x = (real1 * r + imag1) * d;
	y = (imag1 * r - real1) * d;
    }else{
	r = imag2 / real2;
	d = 1.0f / (real2 * (1.0f + r * r));
	x = (real1 + imag1 * r) * d;
	y = (imag1 - real1 * r) * d;
    }
    ((float*)res)[0] = x;
    ((float*)res)[1] = y;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ void
__pgi_cdsqrt( signed char* res, double real1, double imag1 )
{
    double a, x, y;
    a = hypot( real1, imag1 );
    if( a == 0.0 ){
	x = 0.0; y = 0.0;
    }else if( real1 > 0.0 ){
	x = sqrt( 0.5 * (a + real1) );
	y = 0.5 * (imag1 / x);
    }else{
	y = sqrt( 0.5 * (a - real1) );
	if( imag1 < 0.0 ) y = -y;
	x = 0.5 * (imag1 / y);
    }
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cdexp( signed char* res, double real1, double imag1 )
{
    double x, y, z;
    x = exp( real1 );
    sincos( imag1, &z, &y );
    y *= x;
    z *= x;
    ((double*)res)[0] = y;
    ((double*)res)[1] = z;
}

__device__ static __inline__ void
__pgi_cdlog( signed char* res, double real1, double imag1 )
{
    double x, y;
    x = atan2( imag1, real1 );
    y = log( hypot( real1, imag1 ) );
    ((double*)res)[0] = y;
    ((double*)res)[1] = x;
}

__device__ static __inline__ void
__pgi_cdcos( signed char* res, double real1, double imag1 )
{
    double x, y;
    x = cos(real1);
    y = sin(real1);
    x = x * cosh(imag1);
    y = -y * sinh(imag1);
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cdsin( signed char* res, double real1, double imag1 )
{
    double x, y;
    x = sin(real1);
    y = cos(real1);
    x = x * cosh(imag1);
    y = y * sinh(imag1);
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cdpowcd( signed char* res, double real1, double imag1, double real2, double imag2 )
{
    double logr, logi, x, y, z, w;
    logr = log( hypot( real1, imag1 ) );
    logi = atan2( imag1, real1 );

    x = exp( logr * real2 - logi * imag2 );
    y = logr * imag2 + logi * real2;
    z = x * cos(y);
    w = x * sin(y);
    ((double*)res)[0] = z;
    ((double*)res)[1] = w;
}

__device__ static __inline__ void
__pgi_zcdsqrt( double real1, double imag1, signed char* res )
{
    double a, x, y;
    a = hypot( real1, imag1 );
    if( a == 0.0 ){
	x = 0.0; y = 0.0;
    }else if( real1 > 0.0 ){
	x = sqrt( 0.5 * (a + real1) );
	y = 0.5 * (imag1 / x);
    }else{
	y = sqrt( 0.5 * (a - real1) );
	if( imag1 < 0.0 ) y = -y;
	x = 0.5 * (imag1 / y);
    }
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_zcdexp( double real1, double imag1, signed char* res )
{
    double x, y, z;
    x = exp( real1 );
    sincos( imag1, &z, &y );
    y *= x;
    z *= x;
    ((double*)res)[0] = y;
    ((double*)res)[1] = z;
}

__device__ static __inline__ void
__pgi_zcdlog( double real1, double imag1, signed char* res )
{
    double x, y;
    x = atan2( imag1, real1 );
    y = log( hypot( real1, imag1 ) );
    ((double*)res)[0] = y;
    ((double*)res)[1] = x;
}

__device__ static __inline__ void
__pgi_zcdcos( double real1, double imag1, signed char* res )
{
    double x, y;
    x = cos(real1);
    y = sin(real1);
    x = x * cosh(imag1);
    y = -y * sinh(imag1);
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_zcdsin( double real1, double imag1, signed char* res )
{
    double x, y;
    x = sin(real1);
    y = cos(real1);
    x = x * cosh(imag1);
    y = y * sinh(imag1);
    ((double*)res)[0] = x;
    ((double*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_zcdpowcd( double real1, double imag1, double real2, double imag2, signed char* res )
{
    double logr, logi, x, y, z, w;
    logr = log( hypot( real1, imag1 ) );
    logi = atan2( imag1, real1 );

    x = exp( logr * real2 - logi * imag2 );
    y = logr * imag2 + logi * real2;
    z = x * cos(y);
    w = x * sin(y);
    ((double*)res)[0] = z;
    ((double*)res)[1] = w;
}

#endif

__device__ static __inline__ void
__pgi_csqrt( signed char* res, float real1, float imag1 )
{
    float a, x, y;
    a = hypotf( real1, imag1 );
    if( a == 0.0f ){
	x = 0.0f; y = 0.0f;
    }else if( real1 > 0.0f ){
	x = sqrtf( 0.5f * (a + real1) );
	y = 0.5f * (imag1 / x);
    }else{
	y = sqrtf( 0.5f * (a - real1) );
	if( imag1 < 0.0f ) y = -y;
	x = 0.5f * (imag1 / y);
    }
    ((float*)res)[0] = x;
    ((float*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cexp( signed char* res, float real1, float imag1 )
{
    float x, y, z;
    x = expf( real1 );
    sincosf( imag1, &z, &y );
    y *= x;
    z *= x;
    ((float*)res)[0] = y;
    ((float*)res)[1] = z;
}

__device__ static __inline__ void
__pgi_clog( signed char* res, float real1, float imag1 )
{
    float x, y;
    x = atan2f( imag1, real1 );
    y = logf( hypotf( real1, imag1 ) );
    ((float*)res)[0] = y;
    ((float*)res)[1] = x;
}

__device__ static __inline__ void
__pgi_ccos( signed char* res, float real1, float imag1 )
{
    float x, y;
    x = cosf(real1);
    y = sinf(real1);
    x = x * coshf(imag1);
    y = -y * sinhf(imag1);
    ((float*)res)[0] = x;
    ((float*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_csin( signed char* res, float real1, float imag1 )
{
    float x, y;
    x = sinf(real1);
    y = cosf(real1);
    x = x * coshf(imag1);
    y = y * sinhf(imag1);
    ((float*)res)[0] = x;
    ((float*)res)[1] = y;
}

__device__ static __inline__ void
__pgi_cpowi( signed char* res, float real, float imag, int i )
{
    int k;
    float fr, fi, gr, gi, tr, ti;
    fr = 1.0f;
    fi = 0.0f;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0f*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cdiv( res, 1.0f, 0.0f, fr, fi );
    }else{
	((float*)res)[0] = fr;
	((float*)res)[1] = fi;
    }
}

__device__ static __inline__ void
__pgi_cpowk( signed char* res, float real, float imag, long long i )
{
    long long k;
    float fr, fi, gr, gi, tr, ti;
    fr = 1.0f;
    fi = 0.0f;
    gr = real;
    gi = imag;
    k = i;
    if( i < 0 ) k = -i;
    while(k){
	if( k & 1 ){
	    tr = fr*gr - fi*gi;
	    ti = fr*gi + fi*gr;
	    fr = tr;
	    fi = ti;
	}
	k = (unsigned long long)k >> 1;
	tr = gr*gr - gi*gi;
	ti = 2.0f*gr*gi;
	gr = tr;
	gi = ti;
    }
    if( i < 0 ){
	__pgi_cdiv( res, 1.0f, 0.0f, fr, fi );
    }else{
	((float*)res)[0] = fr;
	((float*)res)[1] = fi;
    }
}

__device__ static __inline__ void
__pgi_cpowc( signed char* res, float real1, float imag1, float real2, float imag2 )
{
    float logr, logi, x, y, z, w;
    logr = logf( hypotf( real1, imag1 ) );
    logi = atan2f( imag1, real1 );

    x = expf( logr * real2 - logi * imag2 );
    y = logr * imag2 + logi * real2;
    z = x * cosf(y);
    w = x * sinf(y);
    ((float*)res)[0] = z;
    ((float*)res)[1] = w;
}

__device__ static __inline__ float
__pgi_acosd( float x )
{
    return CNVRTRADF(acosf(x));
}

__device__ static __inline__ float
__pgi_asind( float x )
{
    return CNVRTRADF(asinf(x));
}

__device__ static __inline__ float
__pgi_atan2d( float x, float y )
{
    return CNVRTRADF(atan2f(x,y));
}

__device__ static __inline__ float
__pgi_atand( float x )
{
    return CNVRTRADF(atanf(x));
}

__device__ static __inline__ float
__pgi_cosd( float x )
{
    return cosf(CNVRTDEGF(x));
}

__device__ static __inline__ float
__pgi_sind( float x )
{
    return sinf(CNVRTDEGF(x));
}

__device__ static __inline__ float
__pgi_tand( float x )
{
    return tanf(CNVRTDEGF(x));
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_dacosd( double x )
{
    return CNVRTRADD(acos(x));
}

__device__ static __inline__ double
__pgi_dasind( double x )
{
    return CNVRTRADD(asin(x));
}

__device__ static __inline__ double
__pgi_datan2d( double x, double y )
{
    return CNVRTRADD(atan2(x,y));
}

__device__ static __inline__ double
__pgi_datand( double x )
{
    return CNVRTRADD(atan(x));
}

__device__ static __inline__ double
__pgi_dcosd( double x )
{
    return cos(CNVRTDEGD(x));
}

__device__ static __inline__ double
__pgi_dsind( double x )
{
    return sin(CNVRTDEGD(x));
}

__device__ static __inline__ double
__pgi_dtand( double x )
{
    return tan(CNVRTDEGD(x));
}
#endif

__device__ static __inline__ int
__pgi_idim( int x, int y )
{
    x = x - y ;
    if( x < 0 ) x = 0;
    return x;
}

__device__ static __inline__ long long
__pgi_kdim( long long x, long long y )
{
    x = x - y;
    if( x < 0 ) x = 0;
    return x;
}

__device__ static __inline__ float
__pgi_fdim( float x, float y )
{
    x = x - y;
    if( x < 0 ) x = 0;
    return x;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_ddim( double x, double y )
{
    x = x - y;
    if( x < 0 ) x = 0;
    return x;
}
#endif

__device__ static __inline__ int
__pgi_iffloorx( float x )
{
    int i = x;
    if( x < 0 && i != x ) i = i - 1;
    return i;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ int
__pgi_idfloorx( double x )
{
    int i = x;
    if( x < 0 && i != x ) i = i - 1;
    return i;
}
#endif

__device__ static __inline__ long long
__pgi_kffloorx( float x )
{
    long long i = x;
    if( x < 0 && i != x ) i = i - 1;
    return i;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ long long
__pgi_kdfloorx( double x )
{
    long long i = x;
    if( x < 0 && i != x ) i = i - 1;
    return i;
}
#endif

__device__ static __inline__ int
__pgi_ifceilingx( float x )
{
    int i = x;
    if( x > 0 && i != x ) i = i + 1;
    return i;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ int
__pgi_idceilingx( double x )
{
    int i = x;
    if( x > 0 && i != x ) i = i + 1;
    return i;
}
#endif

__device__ static __inline__ long long
__pgi_kfceilingx( float x )
{
    long long i = x;
    if( x > 0 && i != x ) i = i + 1;
    return i;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ long long
__pgi_kdceilingx( double x )
{
    long long i = x;
    if( x > 0 && i != x ) i = i + 1;
    return i;
}
#endif

__device__ static __inline__ int
__pgi_imodulox( int x, int y )
{
    int q = x / y;
    int r = x - q * y;
    if( r != 0 && ((x < 0 && y > 0) || (x > 0 && y < 0)) )
	r += y;
    return r;
}

__device__ static __inline__ int
__pgi_jmodulox( short x, short y )
{
    int q = x / y;
    int r = x - q * y;
    if( r != 0 && (x ^ y) < 0 )	/* signs differ */
	r += y;
    return r;
}

__device__ static __inline__ long long
__pgi_kmodulox( long x, long y )
{
    long long q = x / y;
    long long r = x - q * y;
    if( r != 0 && (x ^ y) < 0 )	/* signs differ */
	r += y;
    return r;
}

__device__ static __inline__ float
__pgi_fmodulox( float x, float y )
{
    float r = fmodf( x, y );
    if( r != 0 && ((x < 0 && y > 0) || (x > 0 && y < 0)) )
	r += y;
    return r;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_dmodulox( double x, double y )
{
    double r = fmod( x, y );
    if( r != 0 && ((x < 0 && y > 0) || (x > 0 && y < 0)) )
	r += y;
    return r;
}
#endif

__device__ static __inline__ int
__pgi_poppari( int x )
{
    return ( __popc(x) & 1);
}

__device__ static __inline__ unsigned long long
__pgi_popparul( unsigned long long x )
{
    return ( __popcll(x) & 1);
}

__device__ static __inline__ int
__pgi_exponf( float f )
{
    int i;
    i = __float_as_int( f );
    if( (i & ~0x80000000) == 0 )
	return 0;
    else
	return ((i >> 23) & 0xff) - 126;
}

__device__ static __inline__ long long
__pgi_kexponf( float f )
{
    int i;
    i = __float_as_int( f );
    if( (i & ~0x80000000) == 0 )
	return 0;
    else
	return ((i >> 23) & 0xff) - 126;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ int
__pgi_expond( double d )
{
    long long i;
    i = __double_as_longlong( d );
    if( (i & ~0x8000000000000000LL) == 0 )
	return 0;
    else
	return ((i >> 52) & 0x7ff) - 1022;
}

__device__ static __inline__ long long
__pgi_kexpond( double d )
{
    long long i;
    i = __double_as_longlong( d );
    if( (i & ~0x8000000000000000LL) == 0 )
	return 0;
    else
	return ((i >> 52) & 0x7ff) - 1022;
}
#endif

__device__ static __inline__ int
__pgi_kcmp( long long a, long long b )
{
    if( a == b ) return 0;
    if( a < b ) return -1;
    return 1;
}

__device__ static __inline__ int
__pgi_kcmpz( long long a )
{
    if( a == 0 ) return 0;
    if( a < 0 ) return -1;
    return 1;
}

__device__ static __inline__ int
__pgi_kucmp( unsigned long long a, unsigned long long b )
{
    if( a == b ) return 0;
    if( a < b ) return -1;
    return 1;
}

__device__ static __inline__ int
__pgi_kucmpz( unsigned long long a )
{
    if( a == 0 ) return 0;
    return 1;
}

__device__ static __inline__ float
__pgi_fracf( float f )
{
    if( f != 0 ){
	int i;
	i = __float_as_int( f );
	i &= ~0x7f800000;
	i |= 0x3f000000;
	f = __int_as_float( i );
    }
    return f;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_fracd( double f )
{
    if( f != 0 ){
	long long i;
	i = __double_as_longlong( f );
	i &= ~0x7ff0000000000000ll;
	i |= 0x3fe0000000000000ll;
	f = __longlong_as_double( i );
    }
    return f;
}
#endif

__device__ static __inline__ float
__pgi_nearestf( float f, int sign )
{
    /* sign is nonzero meaning nearest in the positive direction */
    int i;
    if( f == 0 ){
	/* smallest positive or negative number */
	i = sign ? 0x00100000 : 0x80100000;
	f = __int_as_float( i );
    }else{
	i = __float_as_int( f );
	if( (i & 0x7f800000) != 0x7f800000 ){
	    /* not nan or inf */
	    if( f < 0 ^ (sign != 0) )
		++i;
	    else
		--i;
	    f = __int_as_float( i );
	}
    }
    return f;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_nearestd( double f, int sign )
{
    /* sign is nonzero meaning nearest in the positive direction */
    long long i;
    if( f == 0 ){
	/* smallest positive or negative number */
	i = sign ? 0x0010000000000000ll : 0x8010000000000000ll;
	f = __longlong_as_double( i );
    }else{
	i = __double_as_longlong( f );
	if( (i & 0x7ff0000000000000ll) != 0x7ff0000000000000ll ){
	    /* not nan or inf */
	    if( f < 0 ^ (sign != 0) )
		++i;
	    else
		--i;
	    f = __longlong_as_double( i );
	}
    }
    return f;
}
#endif

__device__ static __inline__ float
__pgi_rrspacingf( float f )
{
    if( f != 0 ){
	int i, j;
	i = __float_as_int( f );
	j = (i & 0x7f800000) ^ 0x7f800000;
	f *= __int_as_float( j );
	if( f < 0 ) f = -f;
	j = (22 + 127) << 23;
	f *= __int_as_float( j );
    }
    return f;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_rrspacingd( double f )
{
    if( f != 0 ){
	long long i, j;
	i = __double_as_longlong( f );
	j = (i & 0x7ff0000000000000ll) ^ 0x7ff0000000000000ll;
	f *= __longlong_as_double( j );
	if( f < 0 ) f = -f;
	j = (long long)(51 + 1023) << 52;
	f *= __longlong_as_double( j );
    }
    return f;
}
#endif

__device__ static __inline__ float
__pgi_scalef( float f, int i )
{
    int e;
    e = i + 127;
    if( e < 0 )
	e = 0;
    else if( e > 255 )
	e = 255;
    e = e << 23;
    return f * __int_as_float( e );
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_scaled( double f, int i )
{
    long long e;
    e = i + 1023;
    if( e < 0 )
	e = 0;
    else if( e > 2047 )
	e = 2047;
    e = e << 52;
    return f * __longlong_as_double( e );
}
#endif

__device__ static __inline__ float
__pgi_setexpf( float f, int j )
{
    int e;
    if( f != 0 ){
	int i;
	i = __float_as_int( f );
	i &= ~0x7f800000;
	i |= 0x3f800000;
	e = j+126;
	if( e < 0 )
	    e = 0;
	else if( e > 255 )
	    e = 255;
	e = e << 23;
	f = __int_as_float( e ) * __int_as_float( i );
    }
    return f;
}

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_setexpd( double f, int j )
{
    long long e, i;
    if( f != 0 ){
	i = __double_as_longlong( f );
	i &= ~0x7ff0000000000000ll;
	i |= 0x3ff0000000000000ll;
	e = j + 1022;
	if( e < 0 )
	    e = 0;
	else if( e > 2047 )
	    e = 2047;
	e = e << 52;
	f = __longlong_as_double( e ) * __longlong_as_double( i );
    }
    return f;
}
#endif

__device__ static __inline__ float
__pgi_spacingf( float f )
{
    int e, i;
    i = __float_as_int( f );
    e = ((i >> 23) & 0xff) - 23;
    if( e < 1 ) e = 1;
    i = e << 23;
    return __int_as_float( i );
}

#if !defined(V2_3) && !defined(V3_0) && !defined(V3_1) && !defined(V3_2) && !defined(V4_0)
template<class T,enum cudaTextureReadMode readMode> 
__device_builtin__ extern __device__ int4 __itexfetchi1D(texture<T,cudaTextureType1D,readMode>, int4);
template<class T,enum cudaTextureReadMode readMode> 
__device_builtin__ extern __device__ uint4 __utexfetchi1D(texture<T,cudaTextureType1D,readMode>, int4);
template<class T,enum cudaTextureReadMode readMode> 
__device_builtin__ extern __device__ float4 __ftexfetchi1D(texture<T,cudaTextureType1D,readMode>, int4);

template<class T,enum cudaTextureReadMode readMode>
__device__ static __inline__ int
__pgi_texfetchi( texture<T,cudaTextureType1D,readMode> tex, int index )
{
    int4 ii, jj;
    ii.x = index;
    ii.y = 0;
    ii.z = 0;
    ii.w = 0;
    jj = __itexfetchi1D( tex, ii );
    return jj.x;
}

template<class T,enum cudaTextureReadMode readMode>
__device__ static __inline__ unsigned int
__pgi_texfetchu( texture<T,cudaTextureType1D,readMode> tex, int index )
{
    int4 ii;
    uint4 jj;
    ii.x = index;
    ii.y = 0;
    ii.z = 0;
    ii.w = 0;
    jj = __utexfetchi1D( tex, ii );
    return jj.x;
}

template<class T,enum cudaTextureReadMode readMode>
__device__ static __inline__ float
__pgi_texfetchf( texture<T,cudaTextureType1D,readMode> tex, int index )
{
    int4 ii;
    float4 jj;
    ii.x = index;
    ii.y = 0;
    ii.z = 0;
    ii.w = 0;
    jj = __ftexfetchi1D( tex, ii );
    return jj.x;
}

template<class T,enum cudaTextureReadMode readMode>
__device__ static __inline__ double
__pgi_texfetchd( texture<T,cudaTextureType1D,readMode> tex, int index )
{
    int4 ii;
    uint4 jj;
    union{
	uint4 jj;
	double jjd;
    }u;
    ii.x = index;
    ii.y = 0;
    ii.z = 0;
    ii.w = 0;
    jj = __utexfetchi1D( tex, ii );
    u.jj.x = jj.x;
    u.jj.y = jj.y;
    return u.jjd;
}
#endif

#ifdef CUDA_DOUBLE_MATH_FUNCTIONS
__device__ static __inline__ double
__pgi_spacingd( double f )
{
    long long e, i;
    i = __double_as_longlong( f );
    e = ((i >> 52) & 0x7ffll) - 52;
    if( e < 1 ) e = 1;
    i = e << 52;
    return __longlong_as_double( i );
}
#endif

#ifndef CUDA_NO_SM_11_ATOMIC_INTRINSICS
__device__ static __inline__ int
__pgi_atomicAddi( void* address, int val )
{
    return atomicAdd( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicAddu( void* address, unsigned int val )
{
    return atomicAdd( (unsigned int*)address, val );
}

#ifndef CUDA_NO_SM_20_INTRINSICS
__device__ static __inline__ float
__pgi_atomicAddf( void* address, float val )
{
    return atomicAdd( (float*)address, val );
}

__device__ static __inline__ double
__pgi_atomicAddd( void* address, double val )
{
  unsigned long long int *address_as_ull = (unsigned long long int*)address;
  unsigned long long int old = *address_as_ull, assumed;
  do {
    assumed = old;
    old = atomicCAS(address_as_ull, assumed, __double_as_longlong(val +
                             __longlong_as_double(assumed)));
  } while (assumed != old);
  return __longlong_as_double(old);
}
#endif

#ifndef CUDA_NO_SM_12_ATOMIC_INTRINSICS
__device__ static __inline__ unsigned long long
__pgi_atomicAddul( void* address, unsigned long long val )
{
    return atomicAdd( (unsigned long long*)address, val );
}
#endif

__device__ static __inline__ int
__pgi_atomicSubi( void* address, int val )
{
    return atomicSub( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicSubu( void* address, unsigned int val )
{
    return atomicSub( (unsigned int*)address, val );
}

__device__ static __inline__ int
__pgi_atomicExchi( void* address, int val )
{
    return atomicExch( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicExchu( void* address, unsigned int val )
{
    return atomicExch( (unsigned int*)address, val );
}

__device__ static __inline__ float
__pgi_atomicExchf( void* address, float val )
{
    return atomicExch( (float*)address, val );
}

#ifndef CUDA_NO_SM_12_ATOMIC_INTRINSICS
__device__ static __inline__ unsigned long long
__pgi_atomicExchul( void* address, unsigned long long val )
{
    return atomicExch( (unsigned long long*)address, val );
}
#endif

__device__ static __inline__ int
__pgi_atomicMini( void* address, int val )
{
    return atomicMin( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicMinu( void* address, unsigned int val )
{
    return atomicMin( (unsigned int*)address, val );
}

__device__ static __inline__ int
__pgi_atomicMaxi( void* address, int val )
{
    return atomicMax( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicMaxu( void* address, unsigned int val )
{
    return atomicMax( (unsigned int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicIncu( void* address, unsigned int val )
{
    return atomicInc( (unsigned int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicDecu( void* address, unsigned int val )
{
    return atomicDec( (unsigned int*)address, val );
}

__device__ static __inline__ int
__pgi_atomicCASi( void* address, int val, int val2 )
{
    return atomicCAS( (int*)address, val, val2 );
}

__device__ static __inline__ unsigned int
__pgi_atomicCASu( void* address, unsigned int val, unsigned int val2 )
{
    return atomicCAS( (unsigned int*)address, val, val2 );
}

#ifndef CUDA_NO_SM_12_ATOMIC_INTRINSICS
__device__ static __inline__ unsigned long long
__pgi_atomicCASul( void* address, unsigned long long val, unsigned long long val2 )
{
    return atomicCAS( (unsigned long long*)address, val, val2 );
}
#endif

__device__ static __inline__ int
__pgi_atomicAndi( void* address, int val )
{
    return atomicAnd( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicAndu( void* address, unsigned int val )
{
    return atomicAnd( (unsigned int*)address, val );
}

__device__ static __inline__ int
__pgi_atomicOri( void* address, int val )
{
    return atomicOr( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicOru( void* address, unsigned int val )
{
    return atomicOr( (unsigned int*)address, val );
}

__device__ static __inline__ int
__pgi_atomicXori( void* address, int val )
{
    return atomicXor( (int*)address, val );
}

__device__ static __inline__ unsigned int
__pgi_atomicXoru( void* address, unsigned int val )
{
    return atomicXor( (unsigned int*)address, val );
}
#endif

#ifndef CUDA_NO_SM_20_INTRINSICS
/* compute capability 2.0 */
#define __pgi_mul24(i,j)  (i)*(j)
#define __pgi_umul24(i,j)  (i)*(j)
#else
#define __pgi_mul24(i,j)  __mul24(i,j)
#define __pgi_umul24(i,j)  __umul24(i,j)
/* compute capability < 2.0 */
#endif

#ifndef CUDA_NO_SM_20_INTRINSICS
extern __device__ int printf(const char*, ...);

/* F90 IO */
__device__ static __inline__ void
__pgf90io_src_info( void* x, signed char* str, int lineno )
{
    /* stub routine, only used on the host for error reporting */
}

__device__ static __inline__ int
__pgf90io_ldw_init( void* a, void* b, void* c, void* d )
{
    /* stub routine, only used on the host */
    return 0;
}

/* print a character string */
__device__ static __inline__ int
__pgf90io_sc_ch_ldw( void* s, int ftype, int len )
{
    printf( " %s", (char*)s );
    return 0;
}

/* print a complex */
__device__ static __inline__ int
__pgf90io_sc_cd_ldw( double r, double i, int ftype )
{
    printf( " (%f,%f)", r, i );
    return 0;
}

/* print a complex */
__device__ static __inline__ int
__pgf90io_sc_cf_ldw( float r, float i, int ftype )
{
    printf( " (%f,%f)", (double)r, (double)i );
    return 0;
}

/* print a double */
__device__ static __inline__ int
__pgf90io_sc_d_ldw( double d, int ftype )
{
    printf( " %f", d );
    return 0;
}

/* print a float */
__device__ static __inline__ int
__pgf90io_sc_f_ldw( float f, int ftype )
{
    printf( " %f", (double)f );
    return 0;
}

/* print an int */
__device__ static __inline__ int
__pgf90io_sc_i_ldw( int i, int itype )
{
    printf( " %d", i );
    return 0;
}

/* print a logical */
__device__ static __inline__ int
__pgf90io_sc_l_ldw( int i, int itype )
{
    printf( " %s", i == 0 ? "F" : "T" );
    return 0;
}

/* end of line */
__device__ static __inline__ int
__pgf90io_ldw_end()
{
    printf( "\n" );
    return 0;
}
#endif

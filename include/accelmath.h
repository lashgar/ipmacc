/*
 *       Copyright (C) 2009-2011, STMicroelectronics, Incorporated.
 *       All rights reserved.
 *
 *         STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
 *  This software is supplied under the terms of a license agreement
 *  or nondisclosure agreement with STMicroelectronics and may not be
 *  copied or disclosed except in accordance with the terms of that
 *  agreement.
 *
 *         This source code is intended only as a supplement to
 *  STMicroelectronics Development Tools and/or on-line documentation.
 *  See these sources for detailed information about
 *  STMicroelectronics samples.
 *
 *         THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT
 *  WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT
 *  NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR
 *  FITNESS FOR A PARTICULAR PURPOSE. 
 */

/* Tell the compiler about libm functions that are not builtins */

/* float libm functions */
extern float acosf(float);
extern float acoshf(float);
extern float asinf(float);
extern float asinhf(float);
extern float atanhf(float);
extern float atan2f(float,float);
extern float cbrtf(float);
extern float ceilf(float);
extern float copysignf(float,float);
extern float cosf(float);
extern float coshf(float);
extern float erff(float);
extern float erfcf(float);
extern float expf(float);
extern float exp2f(float);
extern float exp10f(float);
extern float expm1f(float);
extern float fabsf(float);
extern float floorf(float);
extern float fmaf(float,float,float);
extern float fminf(float,float);
extern float fmaxf(float,float);
extern int ilogbf(float);
extern float ldexpf(float,int);
extern float lgammaf(float);
extern long long int llrintf(float);
extern long long int llroundf(float);
extern float logbf(float);
extern float log1pf(float);
extern float logf(float);
extern float log2f(float);
extern float log10f(float);
extern long int lrintf(float);
extern long int lroundf(float);
extern float nanf(char*);
extern float nearbyintf(float);
extern float nextafterf(float,float);
extern float powf(float,float);
extern float remainderf(float,float);
extern float remquof(float,float,int*);
extern float rintf(float);
extern float roundf(float);
extern float rsqrtf(float);
extern float scalblnf(float,long int);
extern float scalbnf(float,int);
extern float sinf(float);
extern float sinhf(float);
extern float sqrtf(float);
extern float tanf(float);
extern float tanhf(float);
extern float tgammaf(float);
extern float truncf(float);

#pragma libm (acosf, acoshf, asinf, asinhf, atanhf, atan2f)
#pragma libm (cbrtf, ceilf, copysignf, cosf, coshf)
#pragma libm (erff, erfcf, expf, exp2f, exp10f, expm1f)
#pragma libm (fabsf, floorf, fmaf, fminf, fmaxf)
#pragma libm (ilogbf)
#pragma libm (ldexpf, lgammaf, llrintf, llroundf, logbf, log1pf, logf, log2f, log10f, lrintf, lroundf)
#pragma libm (nanf, nearbyintf, nextafterf)
#pragma libm (powf)
#pragma libm (remainderf, remquof, rintf, rsqrtf)
#pragma libm (scalblnf, scalbnf, sinf, sinhf, sqrtf)
#pragma libm (tanf, tanhf, tgammaf, truncf)

/* double libm functions */
extern double acos(double);
extern double acosh(double);
extern double asin(double);
extern double asinh(double);
extern double atanh(double);
extern double atan2(double,double);
extern double cbrt(double);
extern double ceil(double);
extern double copysign(double,double);
extern double cos(double);
extern double cosh(double);
extern double erf(double);
extern double erfc(double);
extern double exp(double);
extern double exp2(double);
extern double exp10(double);
extern double expm1(double);
extern double fabs(double);
extern double floor(double);
extern double fma(double,double,double);
extern double fmin(double,double);
extern double fmax(double,double);
extern int ilogb(double);
extern double ldexp(double,int);
extern double lgamma(double);
extern long long int llrint(double);
extern long long int llround(double);
extern double logb(double);
extern double log1p(double);
extern double log(double);
extern double log2(double);
extern double log10(double);
extern long int lrint(double);
extern long int lround(double);
extern double nan(char*);
extern double nearbyint(double);
extern double nextafter(double,double);
extern double pow(double,double);
extern double remainder(double,double);
extern double remquo(double,double,int*);
extern double rint(double);
extern double round(double);
extern double rsqrt(double);
extern double scalbln(double,long int);
extern double scalbn(double,int);
extern double sin(double);
extern double sinh(double);
extern double sqrt(double);
extern double tan(double);
extern double tanh(double);
extern double tgamma(double);
extern double trunc(double);

extern int abs(int);

#pragma libm (abs, acos, acosh, asin, asinh, atanh, atan2)
#pragma libm (cbrt, ceil, copysign, cos, cosh)
#pragma libm (erf, erfc, exp, exp2, exp10, expm1)
#pragma libm (fabs, floor, fma, fmin, fmax)
#pragma libm (ilogb)
#pragma libm (ldexp, lgamma, llrint, llround, logb, log1p, log, log2, log10, lrint, lround)
#pragma libm (pow)
#pragma libm (nan, nearbyint, nextafter)
#pragma libm (remainder, remquo, rint, rsqrt)
#pragma libm (scalbln, scalbn, sin, sinh, sqrt)
#pragma libm (tanf, tanhf, tgamma, trunc)

/* Integer builtins */

#define abs(x)	__builtin_abs(x)
extern int __builtin_abs(int);

/* Float builtins */

#define fabsf(x)	__builtin_fabsf(x)
#define acosf(x)	__builtin_acosf(x)
#define asinf(x)	__builtin_asinf(x)
#define atanf(x)	__builtin_atanf(x)
#define atan2f(x,y)	__builtin_atan2f(x,y)
#define cosf(x)		__builtin_cosf(x)
#define coshf(x)	__builtin_coshf(x)
#define expf(x)		__builtin_expf(x)
#define fminf(x,y)	__builtin_fminf(x,y)
#define fmaxf(x,y)	__builtin_fmaxf(x,y)
#define logf(x)		__builtin_logf(x)
#define log10f(x)	__builtin_log10f(x)
#define powf(x,y)	__builtin_powf(x,y)
#define sinf(x)		__builtin_sinf(x)
#define sinhf(x)	__builtin_sinhf(x)
#define sqrtf(x)	__builtin_sqrtf(x)
#define tanf(x)		__builtin_tanf(x)
#define tanhf(x)	__builtin_tanhf(x)

extern float __builtin_fabsf(float);
extern float __builtin_acosf(float);
extern float __builtin_asinf(float);
extern float __builtin_atanf(float);
extern float __builtin_atan2f(float,float);
extern float __builtin_cosf(float);
extern float __builtin_coshf(float);
extern float __builtin_expf(float);
extern float __builtin_fminf(float,float);
extern float __builtin_fmaxf(float,float);
extern float __builtin_logf(float);
extern float __builtin_log10f(float);
extern float __builtin_powf(float,float);
extern float __builtin_sinf(float);
extern float __builtin_sinhf(float);
extern float __builtin_sqrtf(float);
extern float __builtin_tanf(float);
extern float __builtin_tanhf(float);

/* Double builtins */

#define fabs(x)		__builtin_fabs(x)
#define acos(x)		__builtin_acos(x)
#define asin(x)		__builtin_asin(x)
#define atan(x)		__builtin_atan(x)
#define atan2(x,y)	__builtin_atan2(x,y)
#define cos(x)		__builtin_cos(x)
#define cosh(x)		__builtin_cosh(x)
#define exp(x)		__builtin_exp(x)
#define fmin(x,y)	__builtin_fmin(x,y)
#define fmax(x,y)	__builtin_fmax(x,y)
#define log(x)		__builtin_log(x)
#define log10(x)	__builtin_log10(x)
#define pow(x,y)	__builtin_pow(x,y)
#define sin(x)		__builtin_sin(x)
#define sinh(x)		__builtin_sinh(x)
#define sqrt(x)		__builtin_sqrt(x)
#define tan(x)		__builtin_tan(x)
#define tanh(x)		__builtin_tanh(x)

extern double __builtin_fabs(double);
extern double __builtin_acos(double);
extern double __builtin_asin(double);
extern double __builtin_atan(double);
extern double __builtin_atan2(double,double);
extern double __builtin_cos(double);
extern double __builtin_cosh(double);
extern double __builtin_exp(double);
extern double __builtin_fmin(double,double);
extern double __builtin_fmax(double,double);
extern double __builtin_log(double);
extern double __builtin_log10(double);
extern double __builtin_pow(double,double);
extern double __builtin_sin(double);
extern double __builtin_sinh(double);
extern double __builtin_sqrt(double);
extern double __builtin_tan(double);
extern double __builtin_tanh(double);

extern float fdividef(float,float);
extern float __fdividef(float,float);
extern float __fadd_rn(float,float);
extern float __fadd_rz(float,float);
extern float __fadd_ru(float,float);
extern float __fadd_rd(float,float);
extern float __fmul_rn(float,float);
extern float __fmul_rz(float,float);
extern float __fmul_ru(float,float);
extern float __fmul_rd(float,float);
extern float __fmaf_rn(float,float,float);
extern float __fmaf_rz(float,float,float);
extern float __fmaf_ru(float,float,float);
extern float __fmaf_rd(float,float,float);
extern float __frcp_rn(float);
extern float __frcp_rz(float);
extern float __frcp_ru(float);
extern float __frcp_rd(float);
extern float __fdiv_rn(float,float);
extern float __fdiv_rz(float,float);
extern float __fdiv_ru(float,float);
extern float __fdiv_rd(float,float);
extern float __fsqrt_rn(float);
extern float __fsqrt_rz(float);
extern float __fsqrt_ru(float);
extern float __fsqrt_rd(float);
extern float __expf(float);
extern float __exp10f(float);
extern float __logf(float);
extern float __log2f(float);
extern float __log10f(float);
extern float __sinf(float);
extern float __cosf(float);
extern float __tanf(float);
extern float __powf(float,float);
extern float __saturatef(float);

extern double __dadd_rn(double,double);
extern double __dadd_rz(double,double);
extern double __dadd_ru(double,double);
extern double __dadd_rd(double,double);
extern double __dmul_rn(double,double);
extern double __dmul_rz(double,double);
extern double __dmul_ru(double,double);
extern double __dmul_rd(double,double);
extern double __dfma_rn(double,double,double);
extern double __dfma_rz(double,double,double);
extern double __dfma_ru(double,double,double);
extern double __dfma_rd(double,double,double);
extern double __ddiv_rn(double,double);
extern double __ddiv_rz(double,double);
extern double __ddiv_ru(double,double);
extern double __ddiv_rd(double,double);
extern double __drcp_rn(double);
extern double __drcp_rz(double);
extern double __drcp_ru(double);
extern double __drcp_rd(double);
extern double __dsqrt_rn(double);
extern double __dsqrt_rz(double);
extern double __dsqrt_ru(double);
extern double __dsqrt_rd(double);

extern int __mul24(int,int);
extern unsigned int __umul24(unsigned int,unsigned int);
extern int __mulhi(int,int);
extern unsigned int __umulhi(unsigned int,unsigned int);
extern int __mul64hi(int,int);
extern unsigned int __umul64hi(unsigned int,unsigned int);
extern int __sad(int,int,int);
extern unsigned int __usad(unsigned int,unsigned int,unsigned int);
extern int __clz(int);
extern long __clzll(long);
extern int __ffs(int);
extern long __ffsll(long);
extern int __popc(int);
extern long __popcll(long);
extern int __brev(int);
extern long __brevll(long);
extern int __float2int_rn(float);
extern int __float2int_rz(float);
extern int __float2int_ru(float);
extern int __float2int_rd(float);
extern unsigned int __float2uint_rn(float);
extern unsigned int __float2uint_rz(float);
extern unsigned int __float2uint_ru(float);
extern unsigned int __float2uint_rd(float);
extern float __int2float_rn(int);
extern float __int2float_rz(int);
extern float __int2float_ru(int);
extern float __int2float_rd(int);
extern float __uint2float_rn(unsigned int);
extern float __uint2float_rz(unsigned int);
extern float __uint2float_ru(unsigned int);
extern float __uint2float_rd(unsigned int);
extern long __float2ll_rn(float);
extern long __float2ll_rz(float);
extern long __float2ll_ru(float);
extern long __float2ll_rd(float);
extern unsigned long __float2ull_rn(float);
extern unsigned long __float2ull_rz(float);
extern unsigned long __float2ull_ru(float);
extern unsigned long __float2ull_rd(float);
extern float __ll2float_rn(long);
extern float __ll2float_rz(long);
extern float __ll2float_ru(long);
extern float __ll2float_rd(long);
extern float __ull2float_rn(unsigned long);
extern float __ull2float_rz(unsigned long);
extern float __ull2float_ru(unsigned long);
extern float __ull2float_rd(unsigned long);
extern short __float2half_rn(float);
extern float __half2float(short);
extern float __double2float_rn(double);
extern float __double2float_rz(double);
extern float __double2float_ru(double);
extern float __double2float_rd(double);
extern int __double2int_rn(double);
extern int __double2int_rz(double);
extern int __double2int_ru(double);
extern int __double2int_rd(double);
extern unsigned int __double2uint_rn(double);
extern unsigned int __double2uint_rz(double);
extern unsigned int __double2uint_ru(double);
extern unsigned int __double2uint_rd(double);
extern long __double2ll_rn(double);
extern long __double2ll_rz(double);
extern long __double2ll_ru(double);
extern long __double2ll_rd(double);
extern unsigned long __double2ull_rn(double);
extern unsigned long __double2ull_rz(double);
extern unsigned long __double2ull_ru(double);
extern unsigned long __double2ull_rd(double);
extern double __int2double_rn(int);
extern double __uint2double_rn(unsigned int);
extern double __ll2double_rn(long);
extern double __ll2double_rz(long);
extern double __ll2double_ru(long);
extern double __ll2double_rd(long);
extern double __ull2double_rn(unsigned long);
extern double __ull2double_rz(unsigned long);
extern double __ull2double_ru(unsigned long);
extern double __ull2double_rd(unsigned long);

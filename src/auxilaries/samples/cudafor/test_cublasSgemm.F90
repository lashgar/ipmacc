!
!
!      Copyright 2009-2010, STMicroelectronics, Incorporated.
!      All rights reserved.
!
!        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
! This software is supplied under the terms of a license agreement
! or nondisclosure agreement with STMicroelectronics and may not be
! copied or disclosed except in accordance with the terms of that
! agreement.

!
! An example of how to call the cublas single precision matrix multiply
! routine cublasSgemm
!
! Build for running on the host:
!   pgfortran -o test_cublasSgemm_host test_cublasSgemm.F90 -lblas
!
! Build for running on the gpu:
!   pgfortran -Mcuda -D_CUDAFOR -o test_cublasSgemm_gpu test_cublasSgemm.F90 -lcublas
!


program test_cublasSgemm
#ifdef _CUDAFOR
use cudafor

interface
  subroutine sgemm(transa, transb, m, n, k, alpha, a, lda, b, ldb, beta, c, ldc ) bind(c,name='cublasSgemm')
   use iso_c_binding
   integer(c_int), value :: m, n, k, lda, ldb, ldc
   real(c_float), device, dimension(m,n) :: a, b, c
   real(c_float), value :: alpha, beta
   character(kind=c_char), value :: transa, transb
  end subroutine sgemm
end interface

real, device, allocatable, dimension(:,:) :: dA, dB, dC
#endif

real, allocatable, dimension(:,:) :: a, b, c
real :: alpha = 1.0e0
real :: beta  = 0.0e0
real :: t1, t2, tt, gflops
integer :: i, j, k

print *, "Enter N: "
read(5,*) n

allocate(a(n,n), b(n,n), c(n,n))
#ifdef _CUDAFOR
allocate(dA(n,n), dB(n,n), dC(n,n))
#endif

a = 2.0e0
b = 1.5e0
c = -9.9e0

call cpu_time(t1)

#ifdef _CUDAFOR
dA = a
dB = b
if (beta .ne. 0.0) then
  dC = c
endif

call sgemm('n', 'n', n, n, n, alpha, dA, n, dB, n, beta, dC, n)
c = dC
#else
call sgemm('n', 'n', n, n, n, alpha, a, n, b, n, beta, c, n)
#endif

call cpu_time(t2)

print *, "Checking results...."

do j = 1, n
  do i = 1, n
    if (c(i,j) .ne. (3.0e0*real(n))) then
      print *, "error:  ",i,j,c(i,j)
    endif
  enddo
enddo

gflops = (real(n) * real(n) * real(n) * 2.0) / 1000000000.0
tt = t2 - t1
print *, "Total Time: ",tt
print *, "Total SGEMM gflops: ",gflops/tt
print *, "Done...."

end

!
!      Copyright 2009-2012, STMicroelectronics, Incorporated.
!      All rights reserved.
!
!        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
! This software is supplied under the terms of a license agreement
! or nondisclosure agreement with STMicroelectronics and may not be
! copied or disclosed except in accordance with the terms of that
! agreement.

!
! Jacobi iteration example using OpenACC Directives in Fortran
! Build with
!   pgfortran -acc -Minfo=accel -fast f3.f90
!
module sm
contains
 subroutine smooth( a, b, w0, w1, w2, n, m, niters )
  real, dimension(:,:) :: a,b
  real :: w0, w1, w2
  integer :: n, m, niters
  integer :: i, j, iter
   do iter = 1,niters
    !$acc kernels loop
    do i = 2,n-1
     do j = 2,m-1
      a(i,j) = w0 * b(i,j) + &
               w1 * (b(i-1,j) + b(i,j-1) + b(i+1,j) + b(i,j+1)) + &
               w2 * (b(i-1,j-1) + b(i-1,j+1) + b(i+1,j-1) + b(i+1,j+1))
     enddo
    enddo
    !$acc kernels loop
    do i = 2,n-1
     do j = 2,m-1
      b(i,j) = w0 * a(i,j) + &
               w1 * (a(i-1,j) + a(i,j-1) + a(i+1,j) + a(i,j+1)) + &
               w2 * (a(i-1,j-1) + a(i-1,j+1) + a(i+1,j-1) + a(i+1,j+1))
     enddo
    enddo
   enddo
 end subroutine
 subroutine smoothhost( a, b, w0, w1, w2, n, m, niters )
  real, dimension(:,:) :: a,b
  real :: w0, w1, w2
  integer :: n, m, niters
  integer :: i, j, iter
   do iter = 1,niters
    do i = 2,n-1
     do j = 2,m-1
      a(i,j) = w0 * b(i,j) + &
               w1 * (b(i-1,j) + b(i,j-1) + b(i+1,j) + b(i,j+1)) + &
               w2 * (b(i-1,j-1) + b(i-1,j+1) + b(i+1,j-1) + b(i+1,j+1))
     enddo
    enddo
    do i = 2,n-1
     do j = 2,m-1
      b(i,j) = w0 * a(i,j) + &
               w1 * (a(i-1,j) + a(i,j-1) + a(i+1,j) + a(i,j+1)) + &
               w2 * (a(i-1,j-1) + a(i-1,j+1) + a(i+1,j-1) + a(i+1,j+1))
     enddo
    enddo
   enddo
 end subroutine
end module

program main
 use sm
 use openacc
 real,dimension(:,:),allocatable :: aa, bb
 real,dimension(:,:),allocatable :: aahost, bbhost
 real :: w0, w1, w2
 integer :: i,j,n,m,iters
 integer :: c0, c1, c2, c3, cgpu, chost
 integer :: errs, args
 character(10) :: arg
 real :: dif, tol

 n = 0
 m = 0
 iters = 0
 args = command_argument_count()
 if( args .gt. 0 )then
   call get_command_argument( 1, arg )
   read(arg,'(i10)') n
   if( args .gt. 1 )then
    call get_command_argument( 2, arg )
    read(arg,'(i10)') m
    if( args .gt. 2 )then
     call get_command_argument( 3, arg )
     read(arg,'(i10)') iters
     if( args .gt. 3 )then
      call get_command_argument( 4, arg )
      if( arg .eq. 'host' .or. arg .eq. 'HOST' )then
       call acc_set_device( acc_device_host )
       print *, 'set host'
      else if( arg .eq. 'nvidia' .or. arg .eq. 'NVIDIA' )then
       call acc_set_device( acc_device_nvidia )
       call acc_init( acc_device_nvidia )
       print *, 'initialize nvidia'
      else
       print *, 'unknown device:', arg
       print *, 'using default'
      endif
     endif
    endif
   endif
 endif
 if( n .le. 0 ) n = 1000
 if( m .le. 0 ) m = n
 if( iters .le. 0 ) iters = 10

 allocate( aa(n,m) )
 allocate( bb(n,m) )
 allocate( aahost(n,m) )
 allocate( bbhost(n,m) )
 do i = 1,n
   do j = 1,m
     aa(i,j) = 0
     bb(i,j) = i*1000 + j
     aahost(i,j) = 0
     bbhost(i,j) = i*1000 + j
   enddo
 enddo
 w0 = 0.5
 w1 = 0.3
 w2 = 0.2
 call system_clock( count=c1 )
 call smooth( aa, bb, w0, w1, w2, n, m, iters )
 call system_clock( count=c2 )
 cgpu = c2 - c1
 call smoothhost( aahost, bbhost, w0, w1, w2, n, m, iters )
 call system_clock( count=c3)
 chost = c3 - c2
 ! check the results
 errs = 0
 tol = 0.000005
 do i = 1,n
  do j = 1,m
   dif = abs(aa(i,j) - aahost(i,j))
   if( aahost(i,j) .ne. 0 ) dif = abs(dif/aahost(i,j))
   if( dif .gt. tol )then
    errs = errs + 1
    if( errs .le. 10 )then
     print *, i, j, aa(i,j), aahost(i,j)
    endif
   endif
  enddo
 enddo
 print *, errs, ' errors found'
 print *, cgpu, ' microseconds on GPU'
 print *, chost, ' microseconds on host'
end program

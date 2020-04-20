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
! Only slightly less trivial example of PGI Accelerator Directives in Fortran
! Build with
!   pgfortran -ta=nvidia -Minfo=accel -fast f2.f90
!
program main
    use accel_lib
    integer :: n        ! size of the vector
    real,dimension(:),allocatable :: a  ! the vector
    real,dimension(:),allocatable :: r  ! the results
    real,dimension(:),allocatable :: e  ! expected results
    integer :: i
    integer :: c0, c1, c2, c3, cgpu, chost
    character(10) :: arg1
    if( iargc() .gt. 0 )then
        call getarg( 1, arg1 )
        read(arg1,'(i10)') n
    else
        n = 1000000
    endif
    if( n .le. 0 ) n = 1000000
    allocate(a(n))
    allocate(r(n))
    allocate(e(n))
    do i = 1,n
        a(i) = i*2.0
    enddo
    call acc_init( acc_device_nvidia )
    call system_clock( count=c1 )
    !$acc region
        do i = 1,n
            r(i) = sin(a(i)) ** 2 + cos(a(i)) ** 2
        enddo
    !$acc end region
    call system_clock( count=c2 )
    cgpu = c2 - c1
        do i = 1,n
            e(i) = sin(a(i)) ** 2 + cos(a(i)) ** 2
        enddo
    call system_clock( count=c3 )
    chost = c3 - c2
    ! check the results
    do i = 1,n
        if( abs(r(i) - e(i)) .gt. 0.000001 )then
            print *, i, r(i), e(i)
        endif
    enddo
    print *, n, ' iterations completed'
    print *, cgpu, ' microseconds on GPU'
    print *, chost, ' microseconds on host'
end program

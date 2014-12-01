!
!  
! 
!       Copyright 2008-2011, STMicroelectronics, Incorporated.
!       All rights reserved.
! 
!         STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
!  This software is supplied under the terms of a license agreement
!  or nondisclosure agreement with STMicroelectronics and may not be
!  copied or disclosed except in accordance with the terms of that
!  agreement.
!
!          This source code is intended only as a supplement to
!   STMicroelectronics Development Tools and/or on-line documentation.
!   See these sources for detailed information about
!   STMicroelectronics samples.
!
!          THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT
!   WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT
!   NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR
!   FITNESS FOR A PARTICULAR PURPOSE. 
!
! accel_lib.h

      integer accel_version
      parameter ( accel_version = 201003 )
      integer acc_device_none
      parameter ( acc_device_none = 0 )
      integer acc_device_default
      parameter ( acc_device_default = 1 )
      integer acc_device_host
      parameter ( acc_device_host = 2 )
      integer acc_device_not_host
      parameter ( acc_device_not_host = 3 )
      integer acc_device_nvidia
      parameter ( acc_device_nvidia = 4 )

      external acc_get_num_devices
      integer acc_get_num_devices
      external acc_set_device
      external acc_get_device
      integer acc_get_device
      external acc_set_device_num
      external acc_get_device_num
      integer acc_get_device_num
      external acc_init
      external acc_shutdown
      external acc_sync
      external acc_regions
      integer acc_regions
      external acc_kernels
      integer acc_kernels
      external acc_allocs
      integer acc_allocs
      external acc_frees
      integer acc_frees
      external acc_copyins
      integer acc_copyins
      external acc_copyouts
      integer acc_copyouts
      external acc_bytesalloc
      integer(8) acc_bytesalloc
      external acc_bytesin
      integer(8) acc_bytesin
      external acc_bytesout
      integer(8) acc_bytesout
      external acc_get_memory
      integer(8) acc_get_memory
      external acc_get_free_memory
      integer(8) acc_get_free_memory
      external acc_active
      integer(4) acc_active
      external acc_total_time
      integer(8) acc_total_time
      external acc_exec_time
      integer(8) acc_exec_time
      external acc_enable_time
      external acc_disable_time

! 
!       Copyright 2008-2012, STMicroelectronics, Incorporated.
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
! openacc_lib.h

      integer openacc_version
      parameter ( openacc_version = 201111 )
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
      integer pgi_async_sync
      parameter ( pgi_async_sync = 0 )
      integer pgi_async_noval
      parameter ( pgi_async_noval = 0 )

      external acc_get_num_devices
      integer acc_get_num_devices
      external acc_set_device_type
      external acc_get_device_type
      integer acc_get_device_type
      external acc_set_device_num
      external acc_get_device_num
      integer acc_get_device_num
      external acc_async_test
      logical acc_async_test
      external acc_async_test_all
      logical acc_async_test_all
      external acc_async_wait
      external acc_async_wait_all
      external acc_init
      external acc_shutdown
      external acc_on_device
      logical acc_on_device

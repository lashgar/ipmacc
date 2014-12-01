# 
# 
#      Copyright 2009-2012, STMicroelectronics, Incorporated.
#      All rights reserved.
# 
#        STMICROELECTRONICS, INCORPORATED PROPRIETARY INFORMATION
# This software is supplied under the terms of a license agreement
# or nondisclosure agreement with STMicroelectronics and may not be
# copied or disclosed except in accordance with the terms of that
# agreement.
#

#
# just typing 'make' prints out this help message
#
help:
	@echo C Targets include:
	@echo "acc_c1.exe     : first simple example"
	@echo "acc_c2.exe     : second simple example"
	@echo "acc_c2a.exe    : second simple example, executed 3 times"
	@echo "acc_c2i.exe    : second simple example, with acc_init call"
	@echo "acc_c3.exe     : Jacobi relaxation"
	@echo "                 acc_c3 n m iters device"
	@echo "                  [defaults 1000 1000 10 nvidia]"
	@echo "acc_c3a.exe    : Jacobi relaxation with data region"
	@echo "acc_c3i.exe    : Jacobi relaxation without independent clause"
	@echo ""
	@echo Fortran Targets include:
	@echo "acc_f1.exe     : first simple example"
	@echo "acc_f2.exe     : second simple example"
	@echo "acc_f2a.exe    : second simple example, executed 3 times"
	@echo "acc_f2i.exe    : second simple example, with acc_init call"
	@echo "acc_f3.exe     : Jacobi relaxation"
	@echo "                 acc_f3 n m iters device"
	@echo "                  [defaults 1000 1000 10 nvidia]"
	@echo "acc_f3a.exe    : Jacobi relaxation with data region"
	@echo ""
	@echo "xx.uni         : build with -ta=nvidia,host "
	@echo "                   to create PGI Unified Binary for GPU or host"
	@echo "                   xx is any of the above"
	@echo "clean          : remove object, executable files"

#
# make foo.exe builds from foo.c or foo.f90, whichever is available
#

%.exe: %.c
	pgcc -o $@ $< -acc -Minfo=accel -fast
%.exe: %.f90
	pgfortran -o $@ $< -acc -Minfo=accel -fast

#
# make foo.uni builds from foo.c or foo.f90, with -ta=nvidia,host
# which creates a PGI Unified Binary that runs on the host+GPU or just the host

%.uni: %.c
	pgcc -o $@ $< -acc -ta=nvidia,host -Minfo=acc,uni -fast
%.uni: %.f90
	pgfortran -o $@ $< -acc -ta=nvidia,host -Minfo=acc,uni -fast

clean:
	rm -f a.out *.o *.exe *.time *.uni *.gpu *.ptx *.bin *.s *.mod

# 
# 
#      Copyright 2009-2010, STMicroelectronics, Incorporated.
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
	@echo Targets include:
	@echo "c1.exe, f1.exe : first example in C and Fortran"
	@echo "c2.exe, f2.exe : second example in C and Fortran"
	@echo "c3.exe, f3.exe : third example in C and Fortran"
	@echo "xx.time        : build with -ta=nvidia,time to include simple profile library"
	@echo "xx.uni         : build with -ta=nvidia,host to create PGI Unified Binary for GPU or host"
	@echo "                 xx is any of [cf][1-3]"
	@echo "clean          : remove object, executable files"

#
# make foo.exe builds from foo.c or foo.f90, whichever is available
#

%.exe: %.c
	pgcc -o $@ $< -ta=nvidia -Minfo=accel -fast
%.exe: %.f90
	pgfortran -o $@ $< -ta=nvidia -Minfo=accel -fast

#
# make foo.time builds from foo.c or foo.f90, with -ta=nvidia,time
# which links in a simple profiling library
#

%.time: %.c
	pgcc -o $@ $< -ta=nvidia,time -Minfo=accel -fast
%.time: %.f90
	pgfortran -o $@ $< -ta=nvidia,time -Minfo=accel -fast

#
# make foo.uni builds from foo.c or foo.f90, with -ta=nvidia,host
# which creates a PGI Unified Binary that runs on the host+GPU or just the host

%.uni: %.c
	pgcc -o $@ $< -ta=nvidia,host -Minfo -fast
%.uni: %.f90
	pgfortran -o $@ $< -ta=nvidia,host -Minfo -fast



clean:
	rm -f *.o *.exe *.time *.uni *.gpu *.ptx *.bin *.s *.mod

#!/bin/bash

ifeq ($(IPMACCROOT),)
 $(error 'IPMACCROOT is not set, please refer to the README before starting the compilation')
endif

PARALLELBUILD=-j 1
ifneq ($(IPMACCBUILDNCORE), "")
 PARALLELBUILD=-j $(IPMACCBUILDNCORE)
endif

ROOTDIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

ifeq ($(ROOTDIR),)
 $(error "unable to locate Makefile!!")
endif

ifneq (, $(shell which ccache) )
CC="ccache gcc"
CXX="ccache g++"
else
CC=gcc
CXX=g++
endif

libxml2lib=build/lib/libxml2.so
libxsltlib=build/lib/libxslt.so
src2srcmlbin=srcML/bin/src2srcml
uncrustifybin=build/bin/uncrustify
apilib=lib/libopenacc.so
pycparser=parser/utils_clause.py
listdevices=src/listdevices
venv=build/venv/bin/activate

all: $(venv) $(uncrustifybin) $(src2srcmlbin) $(apilib) parser/oaccparser $(listdevices)
	@echo 'all done'

$(venv):
	# use the python on the path to create virtualenv
	virtualenv -p `which python` $(ROOTDIR)/build/venv
	# install modules in env and exit
	. $(ROOTDIR)/build/venv/bin/activate && pip install -r $(ROOTDIR)/requirements.txt && deactivate

$(libxml2lib): # (the compatible version for srcML)
	mkdir -p $(ROOTDIR)/build/extract/libxml2; \
	cd $(ROOTDIR)/build/extract/libxml2; \
	tar xzf $(IPMACCROOT)/vendor-drop/libxml2-2.7.6.tar.gz ; \
	cd libxml2-2.7.6/; \
	CC=$(CC) CXX=$(CXX) ./configure --prefix=$(IPMACCROOT)/build/ > /dev/null; \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null

$(libxsltlib): $(libxml2lib) # (the compatble version for srcML)
	mkdir -p $(ROOTDIR)/build/extract/libxml2; \
	cd $(ROOTDIR)/build/extract/libxml2; \
	tar xzf $(IPMACCROOT)/vendor-drop/libxslt-1.1.26.tar.gz; \
	cd libxslt-1.1.26/; \
	CC=$(CC) CXX=$(CXX) ./configure --prefix=$(IPMACCROOT)/build/ --with-libxml-prefix=$(IPMACCROOT)/build/ > /dev/null;  \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null

# Code standardazing
$(uncrustifybin): $(ROOTDIR)/vendor-drop/uncrustify.tar.gz
	mkdir -p $(ROOTDIR)/build/extract/uncrustify; \
	cd $(ROOTDIR)/build/extract/uncrustify/; \
	tar xvzf $(ROOTDIR)/vendor-drop/uncrustify.tar.gz > /dev/null; \
	cd uncrustify/; \
	make clean > /dev/null; \
	CC=$(CC) CXX=$(CXX) ./configure --prefix=$(ROOTDIR)/build/ > /dev/null; \
	make $(PARALLELBUILD) > /dev/null;  \
	make install > /dev/null; 
	ln -s $(ROOTDIR)/config/avalon.cfg $(ROOTDIR)/build/bin/avalon.cfg 

# Parser
parser/oaccparser:
	make -C $(ROOTDIR)/parser/
	ln -s $(ROOTDIR)/src/utils_clause.py $(ROOTDIR)/parser/

# srcML
$(src2srcmlbin): $(libxsltlib) $(libxml2lib)
	cd $(ROOTDIR)/srcML/ ; \
	tar xzf $(IPMACCROOT)/vendor-drop/srcml.tar.gz > /dev/null ; \
	cd src/ ; \
	make > /dev/null # too shaky for parellel build

# API
$(apilib):
	make -C $(ROOTDIR)/src/ libopenacc

$(listdevices):
	make -C $(ROOTDIR)/src/ listdevices

clean:
	# Parser pycparser
	rm $(ROOTDIR)/parser/utils_clause.pyc $(ROOTDIR)/parser/utils_clause.py -f
	make -C $(ROOTDIR)/parser/ clean
	# srcML
	rm $(ROOTDIR)/srcML/wrapper/wrapper.pyc -f
	rm $(ROOTDIR)/srcML/src -rf
	rm $(ROOTDIR)/srcML/obj -rf
	rm $(ROOTDIR)/srcML/bin -rf
	# srcML libxml2 libxslt uncrustify (Code standardazing)
	rm $(ROOTDIR)/build/ -rf
	rm $(ROOTDIR)/*.pyc -f
	rm $(ROOTDIR)/a.out -f
	# Samples
	rm -f $(ROOTDIR)/test-case/*_ipmacc.cu
	rm -f $(ROOTDIR)/test-case/*_ipmacc.c
	rm -f $(ROOTDIR)/test-case/*.out
	rm -f $(ROOTDIR)/test-case/*.a
	rm -f $(ROOTDIR)/test-case/*.o
	rm -f $(ROOTDIR)/test-case/mand.tga
	make clean -C $(ROOTDIR)/test-case/
	# API
	rm $(ROOTDIR)/lib/ -rf
	make clean -C $(ROOTDIR)/src/


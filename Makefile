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
src2srcmlbin=build/bin/src2srcml
uncrustifybin=build/bin/uncrustify
apilib=build/runtime-lib/libopenacc.so
pycparser=build/extract/pycparser/pycparser/pycparser/c_parser.py
oaccparser=src/parser/oaccparser
listdevices=src/listdevices
venv=build/venv/bin/activate

all: $(venv) $(uncrustifybin) $(src2srcmlbin) $(apilib) $(pycparser) $(oaccparser) $(listdevices)
	@echo 'all done'

$(venv):
	# use the python on the path to create virtualenv
	virtualenv -p `which python` $(ROOTDIR)/build/venv
	# install modules in env and exit
	. $(ROOTDIR)/build/venv/bin/activate && pip install -r $(ROOTDIR)/config/requirements.txt && deactivate

$(libxml2lib): # (the compatible version for srcML)
	mkdir -p $(ROOTDIR)/build/extract/libxml2; \
	cd $(ROOTDIR)/build/extract/libxml2; \
	tar xzf $(IPMACCROOT)/vendor-drop/libxml2-2.7.6.tar.gz ; \
	cd libxml2-2.7.6/; \
	CC=$(CC) CXX=$(CXX) ./configure --prefix=$(IPMACCROOT)/build/ > /dev/null; \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null

$(libxsltlib): $(libxml2lib) # (the compatble version for srcML)
	mkdir -p $(ROOTDIR)/build/extract/libxslt; \
	cd $(ROOTDIR)/build/extract/libxslt; \
	tar xzf $(IPMACCROOT)/vendor-drop/libxslt-1.1.26.tar.gz; \
	cd libxslt-1.1.26/; \
	CC=$(CC) CXX=$(CXX) ./configure --prefix=$(IPMACCROOT)/build/ --with-libxml-prefix=$(IPMACCROOT)/build/ > /dev/null;  \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null

$(pycparser):
	mkdir -p $(ROOTDIR)/build/extract/pycparser; \
	cd $(ROOTDIR)/build/extract/pycparser; \
	tar xzf $(IPMACCROOT)/vendor-drop/pycparser.tar.gz; \
	cd pycparser; \
	mkdir -p $(ROOTDIR)/build/py; \
	cp -r $(ROOTDIR)/build/extract/pycparser/pycparser/pycparser $(ROOTDIR)/build/py

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
$(oaccparser):
	make -C $(ROOTDIR)/src/parser/
	ln -s $(ROOTDIR)/src/utils_clause.py $(ROOTDIR)/src/parser/

# srcML
$(src2srcmlbin): $(libxsltlib) $(libxml2lib)
	mkdir -p $(ROOTDIR)/build/extract/srcML ; \
	cd $(ROOTDIR)/build/extract/srcML ; \
	tar xzf $(IPMACCROOT)/vendor-drop/srcml.tar.gz > /dev/null ; \
	cd src/ ; \
	make > /dev/null ; \
	cp $(ROOTDIR)/build/extract/srcML/bin/src2srcml $(ROOTDIR)/build/bin/ ; \
	cp $(ROOTDIR)/build/extract/srcML/bin/srcml2src $(ROOTDIR)/build/bin/ ; 

# API
$(apilib):
	make -C $(ROOTDIR)/src/ libopenacc
	mkdir -p $(ROOTDIR)/build/runtime-lib
	cp $(ROOTDIR)/src/libopenacc.so $(ROOTDIR)/build/runtime-lib/

$(listdevices):
	make -C $(ROOTDIR)/src/ listdevices

clean:
	# Parser parser
	rm $(ROOTDIR)/src/parser/utils_clause.pyc $(ROOTDIR)/src/parser/utils_clause.py -f
	make -C $(ROOTDIR)/src/parser/ clean
	# srcML
	rm $(ROOTDIR)/src/srcML-wrapper/wrapper.pyc -f
	rm $(ROOTDIR)/srcML/src -rf
	rm $(ROOTDIR)/srcML/obj -rf
	rm $(ROOTDIR)/srcML/bin -rf
	# srcML libxml2 libxslt uncrustify (Code standardazing) pycparser
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


#!/bin/bash

ifeq ($(IPMACCROOT),"")
 $(error 'warning: IPMACCROOT is not set, please refer to the README before starting the compilation')
endif

PARALLELBUILD=-j 1
ifneq ($(IPMACCBUILDNCORE), "")
 PARALLELBUILD=-j $(IPMACCBUILDNCORE)
endif

ROOTDIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

ifeq ($(ROOTDIR), "")
 $(error "unable to locate Makefile!!")
endif

libxml2lib=libxml2/libxml2-2.7.6/build/lib/libxml2.so
libxsltlib=libxml2/libxslt-1.1.26/build/lib/libxslt.so
src2srcmlbin=srcML/bin/src2srcml
uncrustifybin=$(ROOTDIR)/uncrustify/build/bin/uncrustify
apilib=lib/libopenacc.so
pycparser=parser/utils_clause.py


all: venv/bin/activate $(uncrustifybin) $(src2srcmlbin) core $(apilib) parser/oaccparser
	echo 'all done'

venv/bin/activate:
	# use the python on the path to create virtualenv
	virtualenv -p `which python` $(ROOTDIR)/venv
	# install modules in env and exit
	. $(ROOTDIR)/venv/bin/activate; \
	pip install -r $(ROOTDIR)/requirements.txt; \
	deactivate

$(libxml2lib): # (the compatible version for srcML)
	echo '~ compiling libxml2-2.7.6'
	cd $(ROOTDIR)/libxml2; \
	tar xzf libxml2-2.7.6.tar.gz ; \
	cd libxml2-2.7.6/; \
	./configure --prefix=$(IPMACCROOT)/libxml2/libxml2-2.7.6/build/ > /dev/null; \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null
	echo 'done'

$(libxsltlib): $(libxml2lib) # (the compatble version for srcML)
	echo '~ compiling libxslt-1.1.26'
	cd $(ROOTDIR)/libxml2; \
	tar xzf libxslt-1.1.26.tar.gz; \
	cd libxslt-1.1.26/; \
	./configure --prefix=$(IPMACCROOT)/libxml2/libxslt-1.1.26/build --with-libxml-prefix=$(IPMACCROOT)/libxml2/libxml2-2.7.6/build/ > /dev/null;  \
	make $(PARALLELBUILD) > /dev/null; \
	make install > /dev/null
	echo 'done'

# Code standardazing
$(uncrustifybin): $(ROOTDIR)/uncrustify/uncrustify.tar.gz
	echo '~ compiling uncrustify ' 
	cd $(ROOTDIR)/uncrustify/; \
	tar xvzf uncrustify.tar.gz > /dev/null; \
	cd uncrustify/; \
	make clean > /dev/null; \
	./configure --prefix=$(ROOTDIR)/uncrustify/build/ > /dev/null; \
	make $(PARALLELBUILD) > /dev/null;  \
	make install > /dev/null; 
	ln -s $(ROOTDIR)/uncrustify/avalon.cfg $(ROOTDIR)/uncrustify/build/bin/avalon.cfg 
	echo '. done' 

# Parser
parser/oaccparser:
	echo -en '~ compiling pycparser .'
	make -C $(ROOTDIR)/parser/
	echo -en '.'
	ln -s $(ROOTDIR)/src/utils_clause.py $(ROOTDIR)/parser/
	echo '. done'

# srcML
$(src2srcmlbin): $(libxsltlib) $(libxml2lib)
	echo -en '~ compiling srcML parser .'
	cd $(ROOTDIR)/srcML/ ; \
	tar xzf srcml.tar.gz > /dev/null ; \
	cd src/ ; \
	make > /dev/null # too shaky for parellel build
	echo '. done'

# Scanner and CUDA code generator
core:
	cd $(ROOTDIR) ; \
	rm $(ROOTDIR)/preprocessor.py -f ; \
	ln -s $(ROOTDIR)/src/preprocessor-0.1.7b.py $(ROOTDIR)/preprocessor.py ; \
	rm $(ROOTDIR)/scanner.py -f ; \
	ln -s $(ROOTDIR)/src/scanner-0.2.4b.py $(ROOTDIR)/scanner.py ; \
	rm $(ROOTDIR)/codegen.py -f ; \
	ln -s $(ROOTDIR)/src/codegen-0.4.2b.py $(ROOTDIR)/codegen.py

# API
$(apilib):
	echo -en '~ compiling OpenACC API .'
	make -C $(ROOTDIR)/src/ libopenacc
	echo '. done'

clean:
	# python env
	rm $(ROOTDIR)/venv -rf
	# libxml2 libxslt
	rm $(ROOTDIR)/libxml2/libxml2-2.7.6 -rf
	rm $(ROOTDIR)/libxml2/libxslt-1.1.26 -rf
	# Code standardazing
	rm $(ROOTDIR)/uncrustify/uncrustify/ -rf
	rm $(ROOTDIR)/uncrustify/build/ -rf
	# Parser
	# pycparser
	rm $(ROOTDIR)/parser/utils_clause.pyc $(ROOTDIR)/parser/utils_clause.py -f
	make -C $(ROOTDIR)/parser/ clean
	# srcML
	rm $(ROOTDIR)/srcML/wrapper/wrapper.pyc -f
	rm $(ROOTDIR)/srcML/bin -rf
	rm $(ROOTDIR)/srcML/obj -rf
	rm $(ROOTDIR)/srcML/doc -rf
	rm $(ROOTDIR)/srcML/src -rf
	# clean preprocessor, scanner, and code-generator
	rm $(ROOTDIR)/preprocessor.py -f
	rm $(ROOTDIR)/codegen.py -f
	rm $(ROOTDIR)/scanner.py -f
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


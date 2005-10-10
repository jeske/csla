# Copyright (C) 2001 Python Software Foundation

# Makefile to build the html documentation

PYTHONSRC = $(HOME)/projects/python
DOCSRC = $(PYTHONSRC)/Doc
MKHOWTO = $(DOCSRC)/tools/mkhowto

ABOUT = --about $(DOCSRC)/html/stdabout.dat
ADDRESS = --address 'See <i><a href="about.html">About this document...</a></i> for information on suggesting changes.'
UPLINK = --up-link ./index.html
UPTITLE = --up-title "mimelib Documentation"
GLOMOIDX = --global-module-index $(DOCSRC)/modindex.html

OPTIONS = $(ABOUT) $(ADDRESS) $(UPLINK) $(UPTITLE) $(GLOMOIDX)

all: html

html:
	python $(MKHOWTO) $(OPTIONS) libmimelib.tex

clean:
	-rm libmimelib.how libmimelib.ind libmimelib.log
	-rm modlibmimelib.ind *.l2h
	-rm *.pyc

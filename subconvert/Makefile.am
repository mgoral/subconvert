# subconvert/Makefile.am

app_PYTHON = \
	__init__.py \
	apprunner.py \
	resources.py

appdir = $(datadir)/subconvert/subconvert

SUBDIRS = cli gui img parsing utils

CLEANFILES = resources.py resources.pyc
CLEANFILES += *.pyc *.pyo

clean-local:
	rm -rf __pycache__

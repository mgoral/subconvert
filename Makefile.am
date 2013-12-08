# Makefile.am

ACLOCAL_AMFLAGS = -I m4


SUBDIRS = subconvert po

subconvert_SCRIPTS = subconvert.py
subconvertdir = $(datadir)/subconvert

desktop_DATA = subconvert.desktop
desktopdir = $(datadir)/applications

EXTRA_DIST = \
	README.md \
	LICENSE.txt \
	CHANGELOG \
	$(subconvert_SCRIPTS) \
	$(desktop_DATA)

SUBCONVERT_PATH = "./subconvert/"
COVERAGE_DIR = "coverage"

gen:
	$(PYRCC) -py3 -o $(SUBCONVERT_PATH)/resources.py $(SUBCONVERT_PATH)/resources.qrc

test: gen
	@nosetests3 -v

coverage: gen
	@nosetests3 -v --with-coverage --cover-html --cover-html-dir=./coverage --cover-branches --cover-package=subconvert

all: gen

clean-local:
	$(RM) -rf .coverage $(COVERAGE_DIR)

uninstall-hook:
	$(RM) -f $(DESTDIR)$(bindir)/subconvert
	$(RM) -rf $(DESTDIR)$(datadir)/subconvert

install-data-hook:
	$(MKDIR_P) $(DESTDIR)$(bindir)
	cd $(DESTDIR)$(bindir) && \
		$(LN_S) $(DESTDIR)$(datadir)/subconvert/subconvert.py subconvert

reinstall:
	make uninstall
	make install

.PHONY: gen test coverage reinstall

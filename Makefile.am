# Makefile.am

ACLOCAL_AMFLAGS = -I m4


SUBDIRS = subconvert icons img po

subconvert_SCRIPTS = subconvert.py
subconvertdir = $(datadir)/subconvert

desktop_DATA = subconvert.desktop
desktopdir = $(datadir)/applications

EXTRA_DIST = \
	README.md \
	LICENSE.txt \
	CHANGELOG \
	resources.qrc \
	$(subconvert_SCRIPTS) \
	$(desktop_DATA) \
	tools/subconvert_version.sh \
	docs/Makefile \
	docs/*.adoc \
	docs/*.adoc.in \
	docs/manual/*.adoc \
	docs/dev-related/*.adoc \
	docs/changelogs/*.adoc

SUBCONVERT_DIR = ./subconvert
COVERAGE_DIR = "coverage"
VERSION = $(shell sh tools/subconvert_version.sh)

gen:
	$(PYRCC) -o $(SUBCONVERT_DIR)/resources.py resources.qrc
	$(SED) -i 's/__version__ = .\+/__version__ = "$(VERSION)"/' subconvert/utils/version.py

test: gen
	@py.test-3 tests

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

dist-hook:
	echo $(VERSION) > $(distdir)/.tarball-version

reinstall:
	$(MAKE) uninstall
	$(MAKE) install

docs:
	$(MAKE) -C docs

.PHONY: gen test coverage reinstall docs

RM=@rm -rf
MKDIR=@mkdir -p
CP=@cp -r

SUBCONVERT_PATH:="./subconvert/"
COVERAGE_DIR:="coverage"

gen:
	@pyrcc4 -py3 -o $(SUBCONVERT_PATH)/resources.py $(SUBCONVERT_PATH)/resources.qrc

test: gen
	@nosetests3 -v

coverage: gen
	@nosetests3 -v --with-coverage --cover-html --cover-html-dir=./coverage --cover-branches --cover-package=subconvert

all: gen

install: all
	$(MKDIR) build

clean:
	$(RM) ./build
	$(RM) .coverage $(COVERAGE_DIR)
	$(RM) $(SUBCONVERT_PATH)/resources.py
	$(RM) $(shell find . -path .git -prune -o -name "*.mo")

	$(RM) $(shell find . -path .git -prune -o -name "*.pyc")
	$(RM) $(shell find . -path .git -prune -o -name "*.pyo")
	$(RM) $(shell find . -path .git -prune -o -type d -name "__pycache__")

.PHONY: all clean install test gen

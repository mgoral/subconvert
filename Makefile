RM=@rm -rf
MKDIR=@mkdir -p
CP=@cp -r

SUBCONVERT_PATH:="./subconvert/"

gen:
	@pyrcc4 -py3 -o $(SUBCONVERT_PATH)/resources.py $(SUBCONVERT_PATH)/resources.qrc

test: gen
	@nosetests3 -v

all: gen

install: all
	$(MKDIR) build

clean:
	$(RM) ./build
	$(RM) $(SUBCONVERT_PATH)/resources.py
	$(RM) $(shell find . -path .git -prune -o -name "*.mo")

	$(RM) $(shell find . -path .git -prune -o -name "*.pyc")
	$(RM) $(shell find . -path .git -prune -o -type d -name "__pycache__")

.PHONY: all clean install test gen

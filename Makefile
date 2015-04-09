.PHONY: default help

default: help

define helpmsg

The following commands are available:

- Cleanup:

    clean                Clean build artefacts, not docker images.
    cleanall             Clean every container and image.

- Bundle building:

    build PACKAGE=xxx VERSION=yyy

- Other:

    help                 Displays this message.
endef


# Variables
#==========

PYTHON_VERSION ?= 2.7



# Tasks
#======

help:
	$(info $(helpmsg))

build:
	./builder.py --python $(PYTHON_VERSION) $(PACKAGE)==$(VERSION)

clean:
	rm -rf bundles/runner/output

cleanall:
	-docker kill $(shell docker ps -a -q)
	-docker rm -f $(shell docker ps -a -q)
	-docker rmi -f $(shell docker images -a -q)

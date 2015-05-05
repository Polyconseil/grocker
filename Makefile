.PHONY: default help

default: help

define helpmsg

The following commands are available:

- Cleanup:

    clean                Clean build artefacts.
    kill_rm              Kill containers and delete them.
    purge                All of the above and also delete blue solution's images.

- Bundle building:

    build PACKAGE=xxx [VERSION=yyy]

- Other:

    help                 Displays this message.
endef


# Variables
#==========

PYTHON_VERSION ?= 2.7

BLUESOLUTIONS_CONTAINERS := $(shell docker ps |\grep 'bluesolutions' | awk '{print $$1}')
BLUE_REGISTRY_CONTAINERS := $(shell docker ps |\grep 'docker\.polyconseil\.fr' | awk '{print $$1}')

UNTAGGED_IMAGES := $(shell docker images | grep '^<none>' | awk '{print $$3}')
BLUESOLUTIONS_IMAGES := $(shell docker images | grep '^bluesolutions' | awk '{print $$3}')
BLUE_REGISTRY_IMAGES := $(shell docker images | grep '^docker\.polyconseil\.fr' | awk '{print $$3}')


# Tasks
#======

help:
	$(info $(helpmsg))

build:
	./grocker.py --python $(PYTHON_VERSION) $(PACKAGE)==$(VERSION)

clean:
	rm -rf bundles/runner/output

kill_rm:
	-docker kill $(BLUESOLUTIONS_CONTAINERS) $(BLUE_REGISTRY_CONTAINERS)
	-docker rm $(BLUESOLUTIONS_CONTAINERS) $(BLUE_REGISTRY_CONTAINERS)

purge: clean kill_rm
	-docker rmi -f $(BLUESOLUTIONS_IMAGES) $(BLUE_REGISTRY_IMAGES)
	-docker rmi $(UNTAGGED_IMAGES)

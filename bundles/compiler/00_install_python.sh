#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env

# Install System Packages
apt install -qy ${BUILD_DEPS}

# Install Compiler Script
install --mode=0755 --owner=${USER} -D /tmp/01_compile.py ${USER_HOME}/bin/compile.py

# Create Directories
install --mode=0700 --owner=${USER} -d ${USER_HOME}/.pip
install --mode=0700 --owner=${USER} -d ${USER_HOME}/.pip.host
install --mode=0755 --owner=${USER} -d ${USER_HOME}/output

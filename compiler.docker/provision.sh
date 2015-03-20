#!/bin/bash
set -xe

USER=blue
USER_HOME=~blue

BUILD_DEPS="
    build-essential
    gettext

    python-dev
    python3-dev

    nodejs-legacy

    libpq-dev
    libproj-dev

    libjpeg62-turbo-dev
    libffi-dev

    libzbar-dev

    libxml2-dev
    libxslt1-dev

    libldap2-dev
    libsasl2-dev
"

# Install System Packages
export DEBIAN_FRONTEND=noninteractive
alias apt="apt -o APT::Install-Recommends=false -o APT::Install-Suggests=false"

apt install -qy ${BUILD_DEPS}

# Install Compiler Script
install --mode=0755 --owner=${USER} -D /tmp/compiler.py ~blue/bin/compiler.py

# Create Directories
install --mode=0700 --owner=${USER} -d ${USER_HOME}/.pip
install --mode=0700 --owner=${USER} -d ${USER_HOME}/.pip.host
install --mode=0755 --owner=${USER} -d ${USER_HOME}/output

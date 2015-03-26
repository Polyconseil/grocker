#!/bin/bash
set -xe

USER="blue"
GROUP="www-data"

SYS_DEPS="
    nginx-full
    python
    python3
    uwsgi-plugin-python
    uwsgi-plugin-python3
    virtualenv
    sudo
"

BASE_DEPS="
    libpq5
    libgdal1h
    libproj0

    imagemagick
    poppler-utils
    libjpeg62-turbo
    libffi6

    libzbar0

    libxml2
    libxslt1.1

    libldap-2.4-2
    libsasl2-2
"

# TODO: Add our ansiblised debian repository

# Install System Packages
export DEBIAN_FRONTEND=noninteractive
alias apt="apt -o APT::Install-Recommends=false -o APT::Install-Suggests=false"

apt install -qy ${SYS_DEPS} ${BASE_DEPS}

# Create User
adduser --shell /bin/bash --ingroup ${GROUP} --disabled-password --gecos ",,,," ${USER}

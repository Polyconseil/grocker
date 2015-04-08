#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base_vars.sh

# Install System Packages
apt install -qy ${SYS_DEPS} ${BASE_DEPS}
apt-get clean

# Create User
adduser --shell /bin/bash --ingroup ${GROUP} --disabled-password --gecos ",,,," ${USER}

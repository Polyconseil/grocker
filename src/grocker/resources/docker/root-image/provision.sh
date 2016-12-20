#!/bin/sh
set -xe

# Configure system
echo "LANG=C.UTF-8" > /etc/default/locale

# Install System Packages
export DEBIAN_FRONTEND=noninteractive
apt update
apt upgrade -qy
apt install -qy ${SYSTEM_DEPENDENCIES:=}
apt-get clean

# Create grocker user
adduser --shell /bin/bash --disabled-password --gecos ",,,," grocker

# Clean
rm -r $(dirname $0)

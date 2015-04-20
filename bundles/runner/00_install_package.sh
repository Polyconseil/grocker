#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env

# Get target package variables
. /tmp/output/config.env

# Make the environment script available to entrypoint.py
mv /tmp/output/config.env /tmp

# Copy the templates to home directory
mv /tmp/templates/ $USER_HOME

# Create virtualenv with the correct python version in $HOME/app
sudo -u blue virtualenv $USER_HOME/app -p python$PYTHON_VERSION

# Install pip & setuptools
sudo -u blue $USER_HOME/app/bin/pip install pip setuptools --upgrade

# Install the package and its dependencies using the provided wheels
sudo -u blue $USER_HOME/app/bin/pip install --find-links=/tmp/output --no-index $PACKAGE_NAME

# Install the entrypoint script
install --mode=0755 --owner=${USER} -D /tmp/02_entrypoint.py ${USER_HOME}/app/bin/entrypoint.py


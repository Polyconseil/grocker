#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env
source /tmp/output/config.env  # Get target package variables

# Create virtualenv with the correct python version in $HOME/app and update setuptools and pip
sudo -u blue virtualenv ${USER_HOME}/app -p python${PYTHON_VERSION}
sudo -u blue ${USER_HOME}/app/bin/pip install pip setuptools --upgrade

# Install the package and its dependencies using the provided wheels
sudo -u blue ${USER_HOME}/app/bin/pip install --find-links=/tmp/output --no-index ${PACKAGE_NAME}

# Install the entrypoint script and it's dependancies
install --mode=0755 --owner=${USER} -d ${USER_HOME}/etc
install --mode=0644 --owner=${USER} /tmp/output/config.env ${USER_HOME}/etc/config.env
for template in $(ls /tmp/templates/); do
    install --mode=0644 --owner=${USER} -D /tmp/templates/${template} ${USER_HOME}/templates/${template}
done
install --mode=0755 --owner=${USER} -D /tmp/02_entrypoint.py ${USER_HOME}/app/bin/entrypoint.py

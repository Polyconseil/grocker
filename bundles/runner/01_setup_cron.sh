#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env
source ${USER_HOME}/etc/config.env

# Ensure permissions on /var/log/cronwrapper and /var/run/cronwrapper
install --mode=0755 --owner=${USER} --group=${GROUP} -d /var/run/cronwrapper
install --mode=0755 --owner=${USER} --group=${GROUP} -d /var/log/cronwrapper
install --mode=0755 --owner=${USER} -D /tmp/scripts/cronwrapper.sh ${USER_HOME}/bin/cronwrapper.sh

# Cleanup unnecessary files
rm -Rf /tmp/*
rm -Rf /opt/bundle

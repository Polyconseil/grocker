#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env

# Install System Packages
apt update
apt install -qy ${SYS_DEPS} ${BASE_DEPS}
apt-get clean

# Create User
adduser --shell /bin/bash --ingroup ${GROUP} --disabled-password --gecos ",,,," ${USER}

# Enable the user to run cron daemon
echo "${USER} ALL=NOPASSWD: /usr/sbin/cron" >> /etc/sudoers
touch /var/run/crond.pid
chown ${USER}:${GROUP} /var/run/crond.pid

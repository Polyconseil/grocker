#!/bin/bash
set -xe

# Configure system
echo "LANG=C.UTF-8" > /etc/default/locale

# Install System Packages
export DEBIAN_FRONTEND=noninteractive
apt update
apt upgrade -qy
apt install -qy ${SYSTEM_DEPS}
apt-get clean

# Create User and allow it to run crond
adduser --shell /bin/bash --disabled-password --gecos ",,,," grocker
cat <<EOF > /etc/sudoers.d/grocker
grocker ALL=NOPASSWD: /usr/sbin/cron
EOF

# Clean
rm -r $(dirname $0)

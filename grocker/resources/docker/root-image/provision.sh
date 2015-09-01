#!/bin/bash
set -xe

cd $(dirname $0)  # Go to Grocker build dir
[ -e provision.env ] && source provision.env  # Retrieve config vars

# Install System Packages
export DEBIAN_FRONTEND=noninteractive
apt update
apt upgrade -qy
apt install -qy ${RUN_DEPS}
apt-get clean

# Create User and allow it to run crond
adduser --shell /bin/bash --disabled-password --gecos ",,,," grocker
cat <<EOF > /etc/sudoers.d/grocker
grocker ALL=NOPASSWD: /usr/sbin/cron
EOF

# Clean
rm -r $(dirname $0)

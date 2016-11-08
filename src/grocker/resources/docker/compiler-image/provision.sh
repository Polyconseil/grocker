#!/bin/sh
set -xe

cd $(dirname $0)  # Go to Grocker build dir
if [ -e ./provision.env ]; then
    . ./provision.env  # Retrieve config vars
fi

apt install -qy ${SYSTEM_DEPS}
install --mode=0555 --owner=grocker /tmp/grocker/compile.py /home/grocker/compile.py

cp grocker_sudoers /etc/sudoers.d/grocker_sudoers

rm -r $(dirname $0)

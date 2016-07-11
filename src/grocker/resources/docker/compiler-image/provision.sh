#!/bin/bash
set -xe

cd $(dirname $0)  # Go to Grocker build dir
[ -e provision.env ] && source provision.env  # Retrieve config vars

apt install -qy ${SYSTEM_DEPS}
install --mode=0555 --owner=grocker /tmp/grocker/compile.py /home/grocker/compile.py

cp grocker_sudoers /etc/sudoers.d/grocker_sudoers

rm -r $(dirname $0)

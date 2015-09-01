#!/bin/bash
set -xe

cd $(dirname $0)  # Go to Grocker build dir
[ -e provision.env ] && source provision.env  # Retrieve config vars

apt install -qy ${BUILD_DEPS}
install --mode=0555 --owner=grocker /tmp/grocker/compile.py /home/grocker/compile.py

rm -r $(dirname $0)

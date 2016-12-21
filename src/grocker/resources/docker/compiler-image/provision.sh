#!/bin/sh
set -xe

cd $(dirname $0)  # Go to Grocker build dir
if [ -e ./provision.env ]; then
    . ./provision.env  # Retrieve config vars
fi

apt install -qy ${SYSTEM_DEPS}
install --mode=0555 --owner=grocker /tmp/grocker/compile.py /home/grocker/compile.py
install --mode=0777 --owner=grocker -d /home/grocker/packages

rm -r $(dirname $0)

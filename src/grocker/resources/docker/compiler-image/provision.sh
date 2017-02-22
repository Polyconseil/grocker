#!/bin/sh
set -xe

apt install -qy ${SYSTEM_DEPENDENCIES:=}
install --mode=0555 --owner=grocker /tmp/grocker/compile.py /home/grocker/compile.py
install --mode=0777 --owner=grocker -d /home/grocker/packages

rm -r $(dirname $0)

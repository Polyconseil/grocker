#!/bin/sh
set -xe

if which apt; then
    apt install -qy ${SYSTEM_DEPENDENCIES:=}
elif which apk; then
    apk add --no-cache ${SYSTEM_DEPENDENCIES:=}
fi

# Unfortunately alpine does not support long options
install -m 0555 -o grocker /tmp/grocker/compile.py /home/grocker/compile.py
install -m 0777 -o grocker -d /home/grocker/packages

rm -r $(dirname $0)

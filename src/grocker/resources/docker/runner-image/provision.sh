#!/bin/sh
set -xe

GROCKER_USER=grocker
WORKING_DIR=$(dirname $0)

setup_venv() {  # venv runtime *dependencies
    local venv runtime release constraint_arg wheelhouse pip
    venv=$1
    runtime=$2
    shift 2
    release="$*"
    if [ -f ${WORKING_DIR}/constraints.txt ]; then
        constraint_arg="--constraint ${WORKING_DIR}/constraints.txt"
    else
        constraint_arg=""
    fi
    wheelhouse=http://${GROCKER_WHEEL_SERVER_IP:=should-be-defined}/

    pip=${venv}/bin/pip

    ${runtime} -m venv ${venv} || ${runtime} -m virtualenv -p ${runtime} ${venv}
    # Old pip can not deal with constraint file
    ${pip} install --upgrade pip
    ${pip} install --no-cache-dir --upgrade pip setuptools ${constraint_arg}
    ${pip} install --no-cache-dir --find-links=${wheelhouse} --trusted-host=${GROCKER_WHEEL_SERVER_IP} --no-index ${constraint_arg} ${release} --no-compile
}


run_as_user() {  # script_or_function
    local script_or_function
    script_or_function="$*"
    if [ "$(whoami)" = ${GROCKER_USER} ]; then
        ${script_or_function}
    else
        chmod -R go+rX ${WORKING_DIR}  # Allow non-root user to use file in grocker temporary directory
        sync  # sync before running script to avoid "unable to execute /tmp/grocker/provision.sh: Text file busy"
        HOME=/home/${GROCKER_USER} su -c $0 ${GROCKER_USER}  # Run this script as grocker user
        rm -r ${WORKING_DIR}  # clean up
    fi
}


only_run_as_root() {  # script_or_function
    local script_or_function
    script_or_function="$*"
    if [ "$(whoami)" = 'root' ]; then
        ${script_or_function}
    fi
}


provision() {
    setup_venv ~/app.venv \
        ${GROCKER_RUNTIME:=should-be-defined} \
        "${GROCKER_APP:=should-be-defined}[${GROCKER_APP_EXTRAS}]==${GROCKER_APP_VERSION:=should-be-defined}"
}

debian_up() {
    apt update
    apt upgrade -qy
    apt-get clean
}

alpine_up() {
    apk upgrade --no-cache
}

system_provision() {
    # Security updates
    if which apt; then
        debian_up
    elif which apk; then
        alpine_up
    fi
}

only_run_as_root system_provision
run_as_user provision

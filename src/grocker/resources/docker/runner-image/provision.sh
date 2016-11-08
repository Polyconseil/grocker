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
    wheelhouse=http://${GROCKER_PYPI_IP}/

    pip=${venv}/bin/pip

    ${runtime} -m virtualenv -p ${runtime} ${venv}
    # Old pip can not deal with constraint file
    ${pip} install --upgrade pip
    ${pip} install --upgrade pip setuptools ${constraint_arg}
    ${pip} install --find-links=${wheelhouse} --trusted-host=${GROCKER_PYPI_IP} --no-index ${constraint_arg} ${release} --no-compile
}


run_as_user() {  # script_or_function
    local script_or_function
    script_or_function="$*"
    if [ "$(whoami)" == ${GROCKER_USER} ]; then
        ${script_or_function}
    else
        chmod -R go+rX ${WORKING_DIR}  # Allow non-root user to use file in grocker temporary directory
        sync  # sync before running script to avoid "unable to execute /tmp/grocker/provision.sh: Text file busy"
        sudo --preserve-env --set-home -u ${GROCKER_USER} /bin/bash $0  # Run this script with grocker user
        rm -r ${WORKING_DIR}  # clean up
    fi
}


only_run_as_root() {  # script_or_function
    local script_or_function
    script_or_function="$*"
    if [ "$(whoami)" == 'root' ]; then
        ${script_or_function}
    fi
}


provision() {
    setup_venv ~/app.venv ${GROCKER_RUNTIME} ${GROCKER_APP}==${GROCKER_APP_VERSION}
}


system_provision() {
    local sys_config_dir
    sys_config_dir=/home/grocker/sys.cfg

    # TODO(fbochu): .grocker file will be obsolete in next major version, so drop it.
    # install Grocker config file
    install --owner=grocker --mode=0444 /tmp/grocker/.grocker ~grocker/.grocker

    # Allow ssmtp configuration
    rm /etc/ssmtp/ssmtp.conf
    ln -s ${sys_config_dir}/ssmtp.conf /etc/ssmtp/ssmtp.conf

    # Security updates
    apt update
    apt upgrade -qy
    apt-get clean
}

only_run_as_root system_provision
run_as_user provision

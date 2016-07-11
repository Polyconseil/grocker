#!/usr/bin/env bash
set -xe

GROCKER_USER=grocker
WORKING_DIR=$(dirname $0)

function setup_venv() {  # venv runtime *dependencies
    local venv=$1
    local runtime=$2
    shift 2
    local release="$*"
    local constraint_arg=$([ -f ${WORKING_DIR}/constraints.txt ] && echo "--constraint ${WORKING_DIR}/constraints.txt")
    local grocker_pypi_ip=$(cat ${WORKING_DIR}/pypi.ip)
    local wheelhouse=http://${grocker_pypi_ip}/

    local pip=${venv}/bin/pip

    ${runtime} -m virtualenv -p ${runtime} ${venv}
    # Old pip can not deal with constraint file
    ${pip} install --upgrade pip
    ${pip} install --upgrade pip setuptools ${constraint_arg}
    ${pip} install --find-links=${wheelhouse} --trusted-host=${grocker_pypi_ip} --no-index ${constraint_arg} ${release} --no-compile
}

function install_python_app() {
    local runtime=$(cat ~/.grocker | grep runtime | cut -f2- -d:)
    local release=$(cat ~/.grocker | grep release | cut -f2- -d:)
    setup_venv ~/app.venv ${runtime} ${release}
}

function run_as_user() {  # script_or_function
    local script_or_function="$*"
    if [ "$(whoami)" == ${GROCKER_USER} ]; then
        ${script_or_function}
    else
        chmod -R go+rX ${WORKING_DIR}  # Allow non-root user to use file in grocker temporary directory
        sudo -u ${GROCKER_USER} $0  # Run this script with grocker user
        rm -r ${WORKING_DIR}  # clean up
    fi
}


function only_run_as_root() {  # script_or_function
    local script_or_function="$*"
    if [ "$(whoami)" == 'root' ]; then
        ${script_or_function}
    fi
}

function provision() {
    install_python_app
}

function system_provision() {
    local sys_config_dir=/home/grocker/sys.cfg

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

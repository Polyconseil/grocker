#!/usr/bin/env bash
set -xe

GROCKER_USER=grocker
WORKING_DIR=$(dirname $0)

function setup_venv() {  # venv runtime *dependencies
    local venv=$1
    local runtime=$2
    shift; shift
    local release="$*"
    local wheelhouse=$(cat ~/.grocker | grep package-dir | cut -f2- -d: | xargs echo)

    local pip=${venv}/bin/pip

    virtualenv -p ${runtime} ${venv}
    ${pip} install --upgrade pip setuptools
    ${pip} install --no-index --find-links=${wheelhouse} ${release}
}

function install_python_app() {
    local runtime=$(cat ~/.grocker | grep runtime | cut -f2- -d:)
    local release=$(cat ~/.grocker | grep release | cut -f2- -d:)
    setup_venv ~/app.venv ${runtime} ${release}
}

function install_grocker_entrypoint() {
    local entrypoint=$(cat ~/.grocker | grep entrypoint | cut -f2- -d: | xargs echo)
    setup_venv ~/ep.venv python ${entrypoint}
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
    install_grocker_entrypoint
}

function system_provision() {
    local sys_config_dir=/home/grocker/sys.cfg

    # Allow ssmtp configuration
    rm /etc/ssmtp/ssmtp.conf
    ln -s ${sys_config_dir}/ssmtp.conf /etc/ssmtp/ssmtp.conf
}

only_run_as_root system_provision
run_as_user provision

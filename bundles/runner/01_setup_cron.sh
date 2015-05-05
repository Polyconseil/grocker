#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base.env
source ${USER_HOME}/etc/config.env

# Copy crontabs to root, ensure permissions
CRONTAB_FILE=$(${USER_HOME}/app/bin/python -c "import pkg_resources; print(pkg_resources.resource_filename('${PROJECT_NAME}', 'crontab'))")
if [ -f "${CRONTAB_FILE}" ]; then
    cat ${CRONTAB_FILE} | \
    sed -e "s@ www-data @ @" | \
    sed -e "s@ /usr/share/bluesys-cronwrapper/bin/cronwrapper.sh @ ${USER_HOME}/bin/cronwrapper.sh @" | \
    crontab -u ${USER} -
fi;

# Ensure permissions on /var/log/cronwrapper and /var/run/cronwrapper
install --mode=0755 --owner=${USER} --group=${GROUP} -d /var/run/cronwrapper
install --mode=0755 --owner=${USER} --group=${GROUP} -d /var/log/cronwrapper
install --mode=0755 --owner=${USER} -D /tmp/scripts/cronwrapper.sh ${USER_HOME}/bin/cronwrapper.sh

# Cleanup unnecessary files
rm -Rf /tmp/*
rm -Rf /opt/bundle

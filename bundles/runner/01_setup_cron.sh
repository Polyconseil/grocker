#!/bin/bash
set -xe

# Retrieve base variables
source /opt/bundle/base_vars.sh

# Get target package variables
. /tmp/config.env

# Copy crontabs to root, ensure permissions
CRONTAB_FILE=$($USER_HOME/app/bin/python -c "import pkg_resources; print pkg_resources.resource_filename('$PROJECT_NAME', 'crontab')")
cp ${CRONTAB_FILE} /etc/cron.d/app
chown root:root /etc/cron.d/app
chmod 600 /etc/cron.d/app

# Ensure permissions on /var/log/cronwrapper and /var/run/cronwrapper
mkdir /var/run/cronwrapper
mkdir /var/log/cronwrapper
chown ${USER}:${GROUP} /var/log/cronwrapper
chown ${USER}:${GROUP} /var/run/cronwrapper

# Replace variables in the application's crontab
# FIXME: to be changed directly in the application's crontab
sed -i "s@ www-data @ ${USER} @" /etc/cron.d/app
sed -i "s@ \/usr\/share\/bluesys-cronwrapper\/bin\/cronwrapper\.sh @ ${USER_HOME}\/cronwrapper.sh @" /etc/cron.d/app

# Cleanup unnecessary files
rm -Rf /tmp/output
rm -Rf /opt/bundle

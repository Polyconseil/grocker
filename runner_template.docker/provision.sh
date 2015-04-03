#
#    Script to install the SI project into the docker
#
#    for python, the virtualenv is created inside $HOME/app
#
#

set -ex
. /tmp/output/config.env

USER='blue'
BLUE_HOME=$( getent passwd "$USER" | cut -d: -f6 )

sudo -u blue virtualenv $BLUE_HOME/app -p python$PYTHON_VERSION
sudo -u blue $BLUE_HOME/app/bin/pip install pip setuptools --upgrade
sudo -u blue $BLUE_HOME/app/bin/pip install --find-links=/tmp/output --no-index $PACKAGE_NAME

rm -Rf /tmp/output

Bundling
========

Architecture
------------

```bash
.
├── builder.py  ---------------------- contains code to compile the bundles
├── bundles
│   ├── base ------------------------- base bundle, contains shared packages and variables
│   │   ├── 00_apt_config.sh
│   │   ├── 01_provision.sh
│   │   ├── base_vars.sh
│   │   └── Dockerfile
│   ├── compiler --------------------- compiler bundle, contains rules to create a package's wheelhouse
│   │   ├── 00_install_python.sh
│   │   ├── 01_compile.py
│   │   └── Dockerfile
│   └── runner ----------------------- runner bundle, contains rules to execute a wheel package
│       ├── 00_install_package.sh
│       ├── 01_setup_cron.sh
│       ├── 02_entrypoint.py
│       ├── Dockerfile
│       └── templates
│           ├── cronwrapper.sh
│           ├── nginx.conf
│           ├── settings.ini
│           ├── supervisord.conf
│           └── uwsgi.ini
├── Makefile
└── README.rst


```

Prerequisites
-------------

Building Docker images
~~~~~~~~~~~~~~~~~~~~~~

.. note:: **Prerequisite**

  The user running the program should be able to run the docker command.
  On Debian:

      $ sudo usermod -a -G docker ${USER}
      $ sudo service docker restart
      $ su ${USER}

Run the following command to build a package::

  ./builder.py --python <PYTHON_VERSION> <PACKAGE>==<VERSION>

or alternatively::

  make build PACKAGE=milborne VERSION=0.4.0.dev2015041600284


Running Docker images
~~~~~~~~~~~~~~~~~~~~~

Run the 'ops' SI service from the built image with::

  docker run \
    -v <CONFIG_DIR>:/config \
    -v <SCRIPT_DIR>:/scripts \
    -v /dev/log:/dev/log \
    -p 80:8080 -ti bluesolutions/milborne:0.4.0.dev2015041600284 \
    si-service ops

This mounts a /config directory, a /scripts directory, the /dev/log
device, and binds the port 80 of the HOST mcahine to the 8080 port of
the docker machine.

Then we run the si-service named "ops".

.. note:: Port configuration

  The inside nginx acts as a socket proxy towards the internal uwsgi application.
  The runner machine exposes the ports 8080 and 8081 but for now, only 8080
  is used (by nginx)


si-service <SERVICE> command
............................

You can use this command to run any SERVICE of the target system. Examples
are ops, www, ws, priv_apis...

cron command
............

This command fires a live cron daemon which uses the system's internal crontab
to run commands.

shell command
.............

Runs a bash shell as the image's main command.

pyscript <SCRIPT_NAME> [PARAMS] command
.......................................

This command executes a python script from the /scripts folder that you should
have mounted. The python script is executed with the app's python executable,
in its virtual environment, and some environment variables::

  DJANGO_SETTINGS_MODULE: the django settings object path, in dotted notation
  <APP>_CONFIG: the path to the application's settings.ini

The /scripts folder is writable.

django-admin <CMD_NAME> [PARAMS] command
........................................

Similar to the 'pyscript' command, you can execute any of your app's Django
management command by providing its name.


Uploading Docker images
~~~~~~~~~~~~~~~~~~~~~~~

We have a private repository available to the developers.
You can upload to it the images you've built::

  docker tag <IMAGE_ID> docker.polyconseil.fr/APP:VERSION
  docker push docker.polyconseil.fr/APP:VERSION

For instance, 'milborne' could be the APP and '0.4.1.devXXX' the VERSION.


.. note:: Image IDs and Image Tags

  You can find a particular local image ID using `docker images`.

  You can fetch a list of the remote tags for an app on:

    https://docker.polyconseil.fr/v1/repositories/<APP>/tags


Downloading Docker images
~~~~~~~~~~~~~~~~~~~~~~~~~

The docker registry makes that extremely easy for us.
If you're logged in docker.polyconseil.fr::

  docker login docker.polyconseil.fr

Every `docker run` command will try and fetch objects from there
if it doesn't exist locally.

Similarly::

  docker pull docker.polyconseil.fr/APP:VERSION

will download the image locally.


Cleanup
~~~~~~~

Clean up your build environment with::

  make clean

Get rid of your already built machines with::

  make purge

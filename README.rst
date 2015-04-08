Bundling
========

Architecture
------------

```bash

├── builder.py  ---------------------- contains code to compile the bundles
├── bundles
│   ├── base ------------------------- base bundle, contains shared packages and
│   │   ├── 00_apt_config.sh             variables.
│   │   ├── 01_provision.sh
│   │   ├── base_vars.sh
│   │   └── Dockerfile
│   ├── compiler --------------------- compiler bundle, contains additional packages
│   │   ├── 00-provision.sh              and rules to compile a package's Wheelhouse.
│   │   ├── 01-compile.py
│   │   └── Dockerfile
│   └── runner ----------------------- runner bundle: a base bundle with a target package
│       ├── 00_install_package.sh        installed.
│       ├── Dockerfile
│       └── output/
├── Makefile ------------------------- orchestrate everything with a Makefile
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

Running Docker images
~~~~~~~~~~~~~~~~~~~~~

Run the built image with::

  docker run -v <CONFIG_DIR>:/config -v /dev/log:/dev/log -p 80:8080 -ti <IMAGE_TAG> --si-name <PACKAGE> <SERVICE>


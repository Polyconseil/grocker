Advanced usage
==============

Grocker build chain can be customized using the command line interface or the
``.grocker.yml`` file (or the one defined through the ``--config`` parameter). When both
are used, command line arguments take precedence.

The build command line interface
--------------------------------

.. code-block:: console

    Usage: grocker [OPTIONS] COMMAND [ARGS]...

    Options:
      --version      Show the version and exit.
      -v, --verbose
      --help         Show this message and exit.

    Commands:
      build  Build docker image for <release> (version...
      purge  Purge Grocker created Docker stuff

.. code-block:: console

    Usage: grocker build [OPTIONS] RELEASE

      Build docker image for RELEASE (version specifiers can be used).

      RELEASE can either be the name of a project, or the path to a wheel to
      use. In both cases, extra requirements can be applied:

      grocker build your_project[with_extra]==1.2.3

      grocker build /path/to/your_project-1.2.3.whl[with_extra]


    Options:
      -c, --config <filename>         Grocker config file
      -r, --runtime <runtime>         runtime used to build and run this image
      --pip-conf <filename>           pip configuration file used to download
                                      dependencies (by default use pip config
                                      getter)
      --pip-constraint <filename>     pip constraint file used to download
                                      dependencies
      -e, --entrypoint <entrypoint>   Docker entrypoint to use to run this image
      --volume <volume>               Container storage and configuration area
      --port <port>                   Port on which a container will listen for
                                      connections
      --env <env=value>               Additional environment variable for final image
      --image-prefix <uri>            docker registry or account on Docker
                                      official registry to use
      --image-base-name <name>        base name for the image (eg '<image-
                                      prefix>/<image-base-name>:<image-version>')
      -n, --image-name <name>         name used to tag the build image
      --result-file <filename>        yaml file where results (image name, ...)
                                      are written
      --build-dependencies / --no-build-dependencies
                                      build the dependencies
      --build-image / --no-build-image
                                      build the docker image
      --push / --no-push              push the image
      --help                          Show this message and exit.

Actions
~~~~~~~

Grocker splits the build chain into three steps:

1. ``dependencies``, compiles wheels and stores them in a data volume.
2. ``image``, builds the **runner** image using stored wheels.
3. ``push``, pushes the **runner** image on the configured Docker registry (
   only if a docker image prefix is given)

This allows you, for example, to build an image without pushing it, then do some tests,
and after your tests passed push the image.

Pip config
~~~~~~~~~~

The ``--pip-conf`` permits to select a specific pip config file. By default Grocker
uses the user pip config file.

.. _grocker_yml:

``.grocker.yml`` config file
----------------------------

The ``.grocker.yml`` allows to customise Grocker build by setting dependencies among other things.
It is written in YAML. By default, Grocker looks for this file in the current directory. Its default values are:

.. code-block:: yaml

    # .grocker.yml (defaults)
    runtime: alpine/3
    pip_constraint: # optional
    volumes: []
    ports: []
    env: {}
    repositories: {}
    dependencies:
        run: []
        build: []
    docker_image_prefix: # optional
    image_base_name: # optional
    entrypoint_name: grocker-runner

Dependencies
~~~~~~~~~~~~

Two kind of dependencies can be declared those used on the final image (``run``) and
those which will be installed only on the build image (``build``).

Each package declared on those lists will be installed using the system package manager.

Repositories
~~~~~~~~~~~~

Each item of the ``repositories`` mapping is a mapping with two keys:

- ``uri``: The deb line of the repository
- ``key``: The GPG key used to sign this repository packages

The first level mapping key is used as the repository identifier.

Example
~~~~~~~

An example with all options customised:

.. code-block:: yaml

    # .grocker.yml (full example)
    runtime: jessie/2.7
    pip_constraint: constraints.txt
    volumes: ['/data', '/cache']
    ports: [8080, 8081]
    env:
        SOME_ENV_VAR: value of the envvars
        ANOTHER_ENV_VAR: 45
        http_proxy: http://127.0.0.1:8080
    repositories:
        nginx:
            uri: deb http://nginx.org/packages/debian/ jessie nginx
            key: |
                -----BEGIN PGP PUBLIC KEY BLOCK-----
                Version: GnuPG v1.4.11 (FreeBSD)

                mQENBE5OMmIBCAD+FPYKGriGGf7NqwKfWC83cBV01gabgVWQmZbMcFzeW+hMsgxH
                W6iimD0RsfZ9oEbfJCPG0CRSZ7ppq5pKamYs2+EJ8Q2ysOFHHwpGrA2C8zyNAs4I
                QxnZZIbETgcSwFtDun0XiqPwPZgyuXVm9PAbLZRbfBzm8wR/3SWygqZBBLdQk5TE
                fDR+Eny/M1RVR4xClECONF9UBB2ejFdI1LD45APbP2hsN/piFByU1t7yK2gpFyRt
                97WzGHn9MV5/TL7AmRPM4pcr3JacmtCnxXeCZ8nLqedoSuHFuhwyDnlAbu8I16O5
                XRrfzhrHRJFM1JnIiGmzZi6zBvH0ItfyX6ttABEBAAG0KW5naW54IHNpZ25pbmcg
                a2V5IDxzaWduaW5nLWtleUBuZ2lueC5jb20+iQE+BBMBAgAoBQJOTjJiAhsDBQkJ
                ZgGABgsJCAcDAgYVCAIJCgsEFgIDAQIeAQIXgAAKCRCr9b2Ce9m/YpvjB/98uV4t
                94d0oEh5XlqEZzVMrcTgPQ3BZt05N5xVuYaglv7OQtdlErMXmRWaFZEqDaMHdniC
                sF63jWMd29vC4xpzIfmsLK3ce9oYo4t9o4WWqBUdf0Ff1LMz1dfLG2HDtKPfYg3C
                8NESud09zuP5NohaE8Qzj/4p6rWDiRpuZ++4fnL3Dt3N6jXILwr/TM/Ma7jvaXGP
                DO3kzm4dNKp5b5bn2nT2QWLPnEKxvOg5Zoej8l9+KFsUnXoWoYCkMQ2QTpZQFNwF
                xwJGoAz8K3PwVPUrIL6b1lsiNovDgcgP0eDgzvwLynWKBPkRRjtgmWLoeaS9FAZV
                ccXJMmANXJFuCf26iQEcBBABAgAGBQJOTkelAAoJEKZP1bF62zmo79oH/1XDb29S
                YtWp+MTJTPFEwlWRiyRuDXy3wBd/BpwBRIWfWzMs1gnCjNjk0EVBVGa2grvy9Jtx
                JKMd6l/PWXVucSt+U/+GO8rBkw14SdhqxaS2l14v6gyMeUrSbY3XfToGfwHC4sa/
                Thn8X4jFaQ2XN5dAIzJGU1s5JA0tjEzUwCnmrKmyMlXZaoQVrmORGjCuH0I0aAFk
                RS0UtnB9HPpxhGVbs24xXZQnZDNbUQeulFxS4uP3OLDBAeCHl+v4t/uotIad8v6J
                SO93vc1evIje6lguE81HHmJn9noxPItvOvSMb2yPsE8mH4cJHRTFNSEhPW6ghmlf
                Wa9ZwiVX5igxcvaIRgQQEQIABgUCTk5b0gAKCRDs8OkLLBcgg1G+AKCnacLb/+W6
                cflirUIExgZdUJqoogCeNPVwXiHEIVqithAM1pdY/gcaQZmIRgQQEQIABgUCTk5f
                YQAKCRCpN2E5pSTFPnNWAJ9gUozyiS+9jf2rJvqmJSeWuCgVRwCcCUFhXRCpQO2Y
                Va3l3WuB+rgKjsQ=
                =A015
                -----END PGP PUBLIC KEY BLOCK-----
    dependencies:
        run:
            - libzbar0
            - libjpeg62-turbo
            - libffi6
            - libtiff5
            - nginx
        build:
            - libzbar-dev
            - libjpeg62-turbo-dev
            - libffi-dev
            - libtiff5-dev

    docker_image_prefix: docker.example.com
    entrypoint_name: my-runner


Purging Grocker stuffs
----------------------

The ``purge`` command is here to clean Grocker created stuff of your Docker daemon.

.. code-block:: console

    Usage: grocker purge [OPTIONS]

      Purge Grocker created Docker stuff

    Options:
      -a, --all-versions / --only-old-versions
      -f, --including-final-images / --excluding-final-images
      --help                          Show this message and exit.

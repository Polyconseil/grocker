Advanced usage
==============

Grocker build chain can be customized using the command line interface or the
``.grocker.yml`` file (or the one defined through the ``--config`` parameter). When both
are used, command line arguments take precedence.

Command line interface
----------------------

.. code-block:: console

    usage: grocker [-h] [-c CONFIG] [-r RUNTIME] [-e ENTRYPOINT_NAME]
                   [--volume VOLUMES] [--port PORTS] [--pip-conf <file>]
                   [--pip-constraint <file>] [--docker-image-prefix <url>]
                   [--image-base-name <name>] [-n <name>]
                   [--result-file <filename>]
                   [--purge {all,builders,dangling,runners}] [--version] [-v]
                   <action> [<action> ...] <release>

    positional arguments:
      <action>              should be one of dep, img, push, build
      <release>             application to build (you can use version specifier)

    optional arguments:
      -h, --help            show this help message and exit
      -c CONFIG, --config CONFIG
                            Grocker config file
      -r RUNTIME, --runtime RUNTIME
                            runtime used to build and run this image
      -e ENTRYPOINT_NAME, --entrypoint-name ENTRYPOINT_NAME
                            Docker entrypoint to use to run this image
      --volume VOLUMES      Container storage and configuration area
      --port PORTS          Port on which a container will listen for connections
      --pip-conf <file>     pip configuration file used to download dependencies
                            (by default use pip config getter)
      --pip-constraint <file>
                            pip constraint file used to download dependencies
      --docker-image-prefix <url>
                            docker registry or account on Docker official registry
                            to use
      --image-base-name <name>
                            base name for the image (eg '<docker-image-prefix
                            >/<image-base-name>:<image-version>')
      -n <name>, --image-name <name>
                            name used to tag the build image
      --result-file <filename>
                            yaml file where results (image name, ...) are written
      --purge {all,builders,dangling,runners}
      --version             show program's version number and exit
      -v, --verbose         verbose mode

Actions
~~~~~~~

Grocker splits the build chain into three steps:

1. ``dep``, compiles wheels and stores them in a data volume.
2. ``img``, builds the **runner** image using stored wheels.
3. ``push``, pushes the **runner** image on the configured Docker registry (
   only if a docker image prefix is given)

The command line accepts multiple steps and runs all that were specified. The order in
which they are provided does not matter, Grocker runs them like so: ``dep``, ``img``
and ``push``. ``build`` is a shortcut for the whole sequence.

This allows you, for example, to build an image without pushing it, then do some tests,
and after your tests passed push the image.

Purge
~~~~~

The ``--purge`` flag is here to clean image list of your Docker daemon. It takes
one argument which can be:

- ``dangling``, drop dangling images
- ``builders``, drop Grocker build images
- ``runners``, drop Grocker run images
- ``all``, ``dangling`` + ``build`` + ``run``

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
    runtime: python3.4
    pip_constraint: # optional
    volumes: []
    ports: []
    repositories: {}
    dependencies: []
    docker_image_prefix: # optional
    image_base_name: # optional
    entrypoint_name: grocker-runner

Dependencies
~~~~~~~~~~~~

Each entry of the  ``dependencies`` list follow one of this syntax:

- ``my-dependency``, for runtime only dependencies (no build dependency)
- ``my-dependency: my-dependency-dev``, for runtime dependencies with one build dependency
- ``my-dependency: [my-dependency-dev, my-dependency-dev2]``, for runtime dependencies
  with more than one build dependencies

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
    runtime: python2.7
    pip_constraint: constraints.txt
    volumes: ['/data', '/cache']
    ports: [8080, 8081]
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
        - libzbar0: libzbar-dev
        - libjpeg62-turbo: libjpeg62-turbo-dev
        - libffi6: libffi-dev
        - libtiff5: libtiff5-dev
        - nginx
    docker_image_prefix: docker.example.com
    entrypoint_name: my-runner

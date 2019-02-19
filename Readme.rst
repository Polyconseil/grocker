Grocker - a Docker image builder for Python applications
========================================================

*Grocker* allows you to bundle your Python applications as Docker image
while keeping the image size as minimal as possible.

*Grocker* uses ``debian:jessie``, ``debian:stretch`` or ``alpine:latest`` as its
base image.

*Grocker* is hosted on Github at https://github.com/polyconseil/Grocker.
*Grocker* full documentation is available on https://grocker.readthedocs.io/.

Installation
============

1. Install Docker Engine. See `its official documentation <https://docs.docker.com/engine/>`_.
2. Install Grocker with *pip*: ``pip install grocker``.

Basic usage
===========

.. code-block:: console

    $ grocker build ipython==5.0.0 --entrypoint ipython
    $ docker run --rm -ti ipython:5.0.0-<grocker-version>

Direct wheel path
=================

A wheel can also be directly passed to grocker to avoid the need to upload an artefact to
build an image.

Grocker will switch to this mode if a ``/`` is present in the argument. Pip ``extra``
requirements can be used in this mode.

.. code-block:: console

    $ grocker build ./path/to/ipython-7.1.1-py3-none-any.whl[doc] --entrypoint ipython
    $ docker run --rm -ti ipython-doc:7.1.1-<grocker-version>

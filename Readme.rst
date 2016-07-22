Grocker - a Docker image builder for Python applications
========================================================

*Grocker* allows you to bundle your Python applications as Docker image
while keeping the image size as minimal as possible.

*Grocker* uses ``debian:jessie`` as its base image. But we have plans to
allow using a lightweight distribution such as Alpine Linux in a near future.

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

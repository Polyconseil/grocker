:authors: Fabien Bochu
:date: 2016-07-21

Grocker, a Docker build chain for Python applications
=====================================================

.. comment, needed to avoid 'Document or section may not begin with a transition.' error
   on build doc, should be removed to build slides.

----

Who am I
--------

- Senior developer at Polyconseil for 2 years
- Member of the Autolib' [#]_ dev team
- Working on DevOps subjects, among others

.. [#] Paris electric car sharing service

Presenter Notes
---------------

- 6 electric car sharing services
- Micro services (~30 different apps)
- Apps based on web technologies, Django and our own libraries (for business logic)

----

Why we built Grocker
--------------------

- Debian packaging was hell (in 2015)
- Containerized applications are the future!
- OpenShift/Source-To-Image use source not package [#]_

.. [#] I lied, when we built grocker, we did not know this project

Presenter Notes
---------------

- Debian Packaging

  - Need to update metadata by hand
  - Our worst case: 48h to package one application and all its dependencies
  - Applications are deployed once a week,
    two days of packaging -> three days for live tests, bug fixes, testing the bug fixes and deployment
  - *Setuptools* entrypoints do not work (except if all your dependencies are exactly those in your setup.py files)

- Our goal: to deploy all our applications at least once a day

- Why Docker

  - Build dependencies are not installed on production servers
  - Atomics deployments!
  - Resource optimisation (one host = N Docker)

----

Other approaches we have considered
-----------------------------------

- ``pip install`` on server
- Distribution packages
- Dockerfile
- Slug (Heroku like)

Presenter Notes
---------------

- ``pip install`` on a production server, seriously?

  - Build extensions in place (ie on production server)
  - Can fail

- Infrastructure and application dependencies should not be mixed otherwise update of one part
  can be blocked by the other one.

- Dockerfile:

  - Extension building: One RUN command to install build dependencies, build wheels,
    uninstall build dependencies (docker layer, size matters)

- Slug:

  - Separate build and run phases
  - One base image for all applications
  - No system dependencies (they are on the base image)

----

How Grocker works
-----------------

.. image:: ../../workflow.svg

Presenter Notes
---------------

Build phases:

1. Build the *root image* based on ``debian:jessie`` (add system packages for runtime dependencies)
2. Build the *compiler image* based on the *root image* (add system packages marked as build dependencies, install compiler script)
3. Instantiate a container for the *compiler image* to build Python wheels for the application and its dependencies (and store them in a data volume)
4. Build the *runner image* based on the *root image* (install compiled wheels served by a web server [#]_)

In fact, this is more complex, there is one *root image* and one *compiler image* by "config".

.. [#] We use the ``pip --no-index`` to install wheels.


----

Why using a compiler image?
---------------------------

- Wheels, simple and reproducible deployment (see http://pythonwheels.com/ )
- C extensions need dependencies to compile
- Docker layers...

Presenter Notes
---------------

- Wheels and C extensions have to be linked with the same library versions than those used at runtime
- Docker layers: data on layers are never deleted, just masked

----

Current limitations
-------------------

- Root image size: between 200 MB (image used for tests) and 600 MB (for our most cumbersome applications)

  - ``debian:jessie``: 125 MB
  - ``alpine``: 5 MB, but missing zbar

- Can only build packaged applications

----

How to use it
-------------

.. code-block:: console

    $ grocker build ipython==5.0 --entrypoint ipython
    [wait a long time]
    $ docker run --rm -ti ipython:5.0-4.0
    Python 3.4.2 (default, Oct  8 2014, 10:45:20)
    Type "copyright", "credits" or "license" for more information.

    IPython 5.0.0 -- An enhanced Interactive Python.
    ?         -> Introduction and overview of IPython's features.
    %quickref -> Quick reference.
    help      -> Python's own help system.
    object?   -> Details about 'object', use 'object??' for extra details.

    In [1]:

----

How to use it (the other side)
------------------------------

With the default configuration, only working for:
 - Packaged applications
 - Python 3
 - Without runtime dependencies

Otherwise, you will need a config file or to use config flags.

----

I need it!
----------

- Grocker was open-sourced yesterday (2016-07-20)
- sources: https://github.com/polyconseil/grocker
- package: https://pypi.python.org/pypi/grocker
- docs: https://grocker.readthedocs.io/en/latest/

----

Thanks!
-------

.. image:: questions.svg
   :height: 30em

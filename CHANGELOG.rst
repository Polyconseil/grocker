ChangeLog
=========

6.10 (unreleased)
-----------------

- Drop Python 3.5 support since it is not supported anymore (**breaking change**).
- Add Python 3.9 support (for Grocker command).
- Add support for buster/3.9 runtime.


6.9.1 (2021-04-20)
------------------

- optionnal manifest set image hash to None


6.9 (2021-04-13)
----------------

- Drop Python 2.7 support (for Grocker command) **breaking change**
- Retrieving the image hash from manifest is now optional and disabled by default


6.8 (2019-11-18)
----------------

- Add Python 3.8 support (for Grocker command).
- Add support for buster/3.8 runtime.
- Add support for buster/3.7 runtime.
- Add support for alpine/3 runtime and use it by default.
- Deprecate stretch/3.7 runtime (**deprecation warning**).
- Deprecate alpine/3.6 runtime (**deprecation warning**)
- Drop Python 3.4 support since it is not supported anymore (**breaking change**).


6.7 (2019-02-19)
----------------

- Fix pip install error when building an image from a wheel with extra requirements passed from a filepath


6.6 (2019-01-18)
----------------

- Python 3.4 & 3.5 support (for Grocker command) will be dropped in next major version (**deprecation warning**)
- Add support for Python's stretch/3.7 docker image.


6.5 (2018-11-28)
----------------

- Replace "+" signs in python versions by "-" in default image name


6.4 (2018-11-28)
----------------

- Python 2.7 support (for Grocker command) will be dropped in next major version (**deprecation warning**)
- Accept wheel path as release argument


6.3 (2018-05-25)
----------------

- Add support for Python's stretch+3.6 docker image.
- Deprecate stretch/3.5 runtime


6.2.1 (2018-04-16)
------------------

- Use latest pip version (10.0)


6.2 (2018-02-07)
----------------

- Switch to Docker(-py) 3.0


6.1 (2017-11-15)
----------------

- Remove grocker version from the image default tag


6.0 (2017-10-25)
----------------

- Allow to set environment variables on the final image
- Deprecate Jessie runtimes
- Allow to use Debian Jessie (Python 2.7 et 3.4), Debian Stretch (Python 3.5) and Alpine (Python 3.6) as base distribution (**breaking change**)
- Simplify dependency declaration (**breaking change**)
- Manage HTTPError when using get or build image


5.4 (2017-10-12)
----------------

- Use python venv instead of virtualenv in compile image


5.3 (2017-08-21)
----------------

- Support of pip trusted host config in wheel builder.
- Retrieve image manifest digest from registry.


5.2 (2017-07-18)
----------------

- Adds gnupg2 to allow grocker to build stretch images.


5.1 (2017-06-07)
----------------

- Also extract pip's timeout configuration from local pip configuration file


5.0 (2017-03-10)
----------------

- Switch cli to click (**breaking change**)
- Add support for Python 3.6
- Drop obsolete .grocker file
- Switch to docker(-py) 2
- Only manage Grocker created stuff when purging
- Drop cron, ssmtp and sudo specific code
- Add support for alpine base images

4.6 (2016-12-22)
----------------

- Fix shell equality test
- Disable useless pip cache
- Stop using sudo in compiler script

4.5 (2016-12-19)
----------------

- Use env vars to pass pip constraint file to wheel compiler.
- Fix empty config file bug

4.4 (2016-11-22)
----------------

- Add ``--image-base-name`` option to allow customizing the generated image name

4.3.2 (2016-11-09)
------------------

- Fix grocker for releases with extras.
- Make sure most tests run without ``--docker-image-prefix`` hence without cache.

4.3.1 (2016-11-09)
------------------

- **Warning** - This version is broken for extras, use 4.3.2 instead.
- Fix ``compiler-image/provision.sh`` sh syntax. ``source`` replaced by ``.``

4.3 (2016-11-08)
----------------

- **Warning** - This version is broken, use 4.3.2 instead.
- Correctly parse the release string and store extras as label and environment variable
- Use the image defined in the configuration (it still needs to be debian based - for the moment)
- Provision scripts now only require sh (instead of bash previously)
- Correctly parse OSX docker client output

4.2 (2016-10-13)
----------------

- Add a sync after chmod call to avoid an AUFS issue
- Fix image search when repoTags is None and not an empty list
- Use env vars to expose grocker meta-data to the application
- Expose some meta-data using image labels
- Use docker build args to pass some build parameters
- Add application venv bin in PATH

4.1 (2016-09-19)
----------------

- Ask for a specific verison of the Docker API (1.21)
- Exclude docker-py 1.10.x (require requests < 2.11)

4.0 (2016-07-20)
----------------

- Drop predefined extra apt repositories
- Drop predefined exposed ports and volumes
- tags: Rename ``grocker.step`` into ``grocker.image.kind``
- Keep the hash type (``sha256``) in the result file

Grocker 3.0.1 (2016-06-06)
--------------------------

- Allow pip_constraint to be a relative path

Grocker 3.0.0 (2016-06-06)
--------------------------

- Also use the constraint file to upgrade pip and setuptools in the app venv
- Add pip_constraint entry to config yaml file
- Remove default dependencies list
- Make --docker-image-prefix optional
- Merge entrypoint into app

Grocker 2.4.2 (2016-04-11)
--------------------------

Grocker 2.4.1 (2016-04-11)
--------------------------

- Fix the use of grocker as a library (broken in previous release)

Grocker 2.4.0 (2016-04-11)
--------------------------

- Only install needed runtime in images
- Allow to set system dependencies by project
- Remove dependencies to host UID

Grocker 2.3.1 (2016-03-03)
--------------------------

- Use Python 3 in entry point venv when runtime is `python3` (fix).

Grocker 2.3.0 (2016-03-03)
--------------------------

- Ask for a specific python version

Grocker 2.2.0 (2016-02-24)
--------------------------

- Allow grocker to be used as a library
- Use common package cache dir for all grocker instances

Grocker 2.1.0 (2016-02-11)
--------------------------

- Add libyaml to run dependencies
- Stop process on build error
- Fix Python 3 support

Grocker 2.0.1
-------------

- Add docker-machine support

Grocker 2.0.0
-------------

- Grocker v2 first release

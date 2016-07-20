ChangeLog
=========

4.1 (unreleased)
----------------

- Nothing changed yet.


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

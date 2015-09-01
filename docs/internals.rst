Fonctionnement interne
======================

Arborescence de *Grocker*::

  .
  ├── grocker  ----------------------------------------- code pour compiler les bundles
  │   ├── builders.py
  │   ├── helpers.py
  │   ├── __init__.py
  │   ├── loggers.py
  │   ├── __main__.py
  │   ├── resources
  │   │   └── docker
  │   │       ├── compiler-image  ---------------------- compiler, utilisé pour builder l'application
  │   │       │   ├── compile.py
  │   │       │   ├── Dockerfile.j2
  │   │       │   ├── provision.env -> ../provision.env
  │   │       │   └── provision.sh
  │   │       ├── provision.env
  │   │       ├── root-image  -------------------------- bundle de base, rootfs
  │   │       │   ├── apt-setup.sh
  │   │       │   ├── Dockerfile
  │   │       │   ├── provision.env -> ../provision.env
  │   │       │   └── provision.sh
  │   │       └── runner-image  ------------------------ runner, dans lequel on installe les wheels buildés.
  │   │           ├── Dockerfile.j2
  │   │           └── provision.sh
  │   └── six.py
  ├── Makefile
  ├── MANIFEST.in
  ├── Readme.rst
  ├── requirements-dev.txt
  ├── requirements.txt
  ├── setup.cfg
  └── setup.py


Déboguage
---------

Lancer un shell dans un container exécuté
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Il est possible de lancer un *shell* dans un conteneur déjà lancé

.. code-block:: bash

  $ docker ps  # trouvez le nom ou l'ID du container qui vous intéresse
  $ docker exec -ti <CONTAINER_NAME> /bin/bash

Eh hop, vous voilà avec un *shell bash* dans ce conteneur. Vous serez sous l'utilisateur *blue*.


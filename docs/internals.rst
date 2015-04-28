Fonctionnement interne
======================

Arborescence de *Grocker*::

  .
  ├── grocker.py  ---------------------- code pour compiler les bundles
  ├── bundles
  │   ├── base ------------------------- bundle de base, rootfs
  │   │   ├── 00_apt_config.sh
  │   │   ├── 01_provision.sh
  │   │   ├── base.env
  │   │   └── Dockerfile
  │   ├── compiler --------------------- compiler, utilisé pour builder l'application
  │   │   ├── 00_install_python.sh
  │   │   ├── 01_compile.py
  │   │   └── Dockerfile
  │   └── runner ----------------------- runner, dans lequel on installe les wheels buildés.
  │       ├── 00_install_package.sh
  │       ├── 01_setup_cron.sh
  │       ├── 02_entrypoint.py
  │       ├── Dockerfile
  │       └── templates
  │           ├── cronwrapper.sh
  │           ├── nginx.conf
  │           ├── settings.ini
  │           ├── supervisord.conf
  │           └── uwsgi.ini
  ├── Makefile
  └── README.rst


Déboguage
---------

Lancer un shell dans un container exécuté
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Il est possible de lancer un *shell* dans un conteneur déjà lancé

.. code-block:: bash

  $ docker ps  # trouvez le nom ou l'ID du container qui vous intéresse
  $ docker exec -ti <CONTAINER_NAME> /bin/bash

Eh hop, vous voilà avec un *shell bash* dans ce conteneur. Vous serez sous l'utilisateur *blue*.


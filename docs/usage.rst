Utilisation des bundles
=======================

Architecture
------------

Arborescence du dossier `builder`::

  .
  ├── builder.py  ---------------------- code pour compiler les bundles
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



Les bundle sont créés via un 'builder'.
Il s'agit d'une build-chain qui s'occupe de péparer, compiler, et installer un SI
ou autre projet (au sens projet hébergé sur Github) dans un container docker.

Le fonctionnement de la création est detaillé dans :doc:`bundling` .


Creation
--------

.. note:: **Prérequis**

  Pour pouvoir lancer la commande 'docker' sans droits super-utilisateur, sous Debian::

      sudo usermod -a -G docker ${USER}
      sudo service docker restart
      su ${USER}


La création de l'image se fait via la commande "builder.py"::

    ./builder.py --python {2.7,3.4} {project}=={version}


L'outil repose sur les tags de version de paquets python disponibles sur notre repository pypi privé.
Par exemple, pour créer une image milborne::

    ./builder.py --python 2.7 milborne==0.4.0.dev2015041600283

De manière équivalente, vous pouvez utiliser le Makefile::

    make build PACKAGE=milborne VERSION=0.4.0.dev2015041600283



Utilisation
-----------

Un bon exemple étant plus parlant, lancez le service 'ops' de milborne comme suit::

  docker run \
    -v <CONFIG_DIR>:/config \
    -v <SCRIPT_DIR>:/scripts \
    -v /dev/log:/dev/log \
    -p 80:8080 -ti docker.polyconseil.fr/milborne:0.4.0.dev2015041600284 \
    start ops

Cette commande monte dans le container un dossier /config, un dossier /scripts,
le device /dev/log, et redirige le port 80 de la machine hôte vers le port 8080 du container.

Puis elle lance le service 'ops' de l'image *docker.polyconseil.fr/milborne:0.4.0.dev2015041600284*
grâce à la commande ``start``.


Ports
~~~~~

Les images embarquant un SI au sens "site web" utilisent le port 8080 en écoute en *interne*. Il faut binder ce port sur la VM, par exemple::

    docker run -p 80:8080 -ti docker.polyconseil.fr/autoslave start ops

.. note:: Configuration de ports

  Le nginx interne au container est un simple proxy vers le SI qui tourne comme une
  application uwsgi.
  Le bundle de run expose les ports 8080 et 8081 mais pour l'instant, seul 8080 est utilisé.


Volumes
~~~~~~~

L'image docker permet de monter différents volumes.

/media
......

Contient les fichiers crées par les utilisateurs (par exemple les permis sur autolib).

/scripts
........

Ce volume est utilisé dans les cas ou nous devons exécuter un script fourni par les développeurs.
Il contiendra lesdits scripts, et après exécution peut contenir des fichiers créés par ces derniers.

.. note:: Montage du dossier /scripts

  Le dossier /scripts, pour être inscriptible par l'utilisateur 'blue' qui execute tout
  dans le container, dit être au préalable créé puis changé au UID 1000 (celui de 'blue')
  afin d'etre inscriptible::

      mkdir /tmp/scripts
      cp xxx.py /tmp/scripts
      chown -R 1000 /tmp/scripts
      docker run -v /tmp/scripts:/scripts [...]

/config
.......

Contient les configurations métier à utiliser pour utiliser le bundle correctement.
Les configurations du SI en particulier sont déposéers dans */config/app/XXX_xxx.ini*.
Un fichier de configuration de base existe et est prefixé par 50; l'ordre alphabétique
compte lors du chargement des fichiers, un préfixe supérieur surchargera la configuration::

    config/
    └── app
        ├── 10_low_priority.ini
        ├── 50_default_settings.ini
        └── 90_override.ini

/dev/log
........

Monte un device de log (a priori, le */dev/log* de la machine hôte) pour le rendre disponible
dans le container.


Commandes
~~~~~~~~~

Les images docker ont un point d'entrée unique avec des commandes simples, décrites ci-dessous.

start <SERVICE>
...............

Utilisez cette commande pour lancer n'importe quel service du SI dans le container.
Exemples:  ops, www, ws, priv_apis...

cron
....

Exécutes un démon cron en avant-plan qui utilise la crontab du SI pour exécuter ses commandes.

[<commande> [<args>]]
.....................

Lance le script, la commande ou un shell dans le conteneur. Dans tous les cas, l'environnement propre au lancement de
l'application est mis en place (activation du venv Python, mise en place des variables d'environnement du project, ...)

- Si l'image est lancée sans argument, un shell (bash) sera lancé.
- Si il existe un fichier dans le dossier /scripts (qui doit donc être monté dans le container) qui à le même nom que
  la commande alors celui-ci sera appelé. Dans ce cas, ce script *doit* commencer par un shebang classique
  (par exemple `#!/usr/bin/bash` ou `#!/usr/bin/env python`).
- Dans les autres cas la commande sera lancé.

Par exemple, les migrations de Django se lancent de la façon suivante : ``<command docker> django-admin.py migrate``.


Registry Docker Privé
---------------------

Nous avons mis en place un repository d'images docker privé pour l'utilisation
en dev, accessible à:

  https://docker.polyconseil.fr/


Upload
~~~~~~

Uploadez une image construite avec les commandes::

  docker tag <IMAGE_ID> docker.polyconseil.fr/APP:VERSION
  docker push docker.polyconseil.fr/APP:VERSION

Par exemple, 'milborne' pourrait être l'APP et '0.4.1.devXXX' la VERSION.


.. note:: Image IDs & Image Tags

  Retrouvez les ID d'images locaux grâce à `docker images`.

  Récupérez une liste de tags distants avec::

    https://docker.polyconseil.fr/v1/repositories/<APP>/tags


Download
~~~~~~~~

L'opération est extrêmement simple grâce au registry.
Si vous êtes enregistrés sur docker.polyconseil.fr::

  docker login docker.polyconseil.fr

...alors chaque commande `docker run` essaiera de récupérer les images
depuis ce registry si non trouvée en local.

De la même manière::

  docker pull docker.polyconseil.fr/APP:VERSION

téléchargera l'image localement.


Tips & Tricks
-------------

Quelques ajouts pour des usages plus avancés.


Lancer un shell dans un container exécuté
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Si parfois vous voulez inspecter un container qui est déjà lancé::

  docker ps  # trouvez le nom ou l'ID du container qui vous intéresse
  docker exec -ti <CONTAINER_NAME> bash

Eh hop, vous voilà avec un shell bash dans ce container. Vous serez
sous l'utilisateur blue cependant, mais des releases suivantes de
docker-engine apporteront la possibilité d'être root::

    https://github.com/docker/docker/pull/12025


Cleanup
~~~~~~~

Clean up your build environment with::

  make clean

Get rid of your already built machines with::

  make purge


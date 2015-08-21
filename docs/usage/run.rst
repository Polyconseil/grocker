Utilisation d'une image
=======================

Interface avec la machine hôte
------------------------------

Les images *Grocker* interagissent avec la machine hôte au travers des interfaces suivantes :

 - les volumes "montés" par *Docker* ;
 - les ports "attachés" par *Docker*.

+-------------------------------------------------------------------------------------------------------------+
| Liste des ports utilisés                                                                                    |
+----------------+--------------------------------------------------------------------------------------------+
| Numéro de port | Utilisation                                                                                |
+================+============================================================================================+
| 8080           | Port d'écoute du service applicatif (si l'instance fournit un service applicatif).         |
+----------------+--------------------------------------------------------------------------------------------+
| 8081           | Port d'écoute du service de supervision (si l'instance fournit un service de supervision.) |
+----------------+--------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------+
| Liste des volumes utilisés                                                                                    |
+------------------+------+-------------------------------------------------------------------------------------+
| Point de montage | Mode | Utilisation                                                                         |
+==================+======+=====================================================================================+
| ``/config``      | *RO* | Contient la configuration technique de l'application.                               |
+------------------+------+-------------------------------------------------------------------------------------+
| ``/media``       | *RW* | Contient les fichiers crées par les utilisateurs (permis de conduire, photos, ...). |
+------------------+------+-------------------------------------------------------------------------------------+
| ``/scripts``     | *RW* | Contient les scripts et leurs sorties (voir :ref:`run-scripts`).                    |
+------------------+------+-------------------------------------------------------------------------------------+
| ``/dev/log``     | *WO* | Permet l'utilisation du service *syslog* de la machine hôte.                        |
+------------------+------+-------------------------------------------------------------------------------------+

Configuration
-------------

La configuration de l'application doit être déposée dans le sous-dossier ``app`` du dossier de configuration. Un fichier de configuration de base est fourni par l'image *Grocker*, celui-ci a une priorité de 50, il est possible de le surcharger en utilisant des fichiers de priorité supérieure::

    config
    ├── ssh-dir
    │   ├── known_hosts
    │   ├── id_rsa
    │   └── ...
    └── app
        ├── 10_low_priority.ini
        ├── 50_default_settings.ini
        └── 90_override.ini

.. note::

  Tous les fichiers contenus au premier niveau de ssh-dir sont copiés dans le dossier ``~/.ssh`` du container à l'installation de l'applicatif. Toute modification de la configuration SSH nécessite donc un redémarrage du docker pour pouvoir être prise en compte.

Commandes
---------

Les images *Grocker* ont un point d'entrée unique avec les commandes simples décrites ci-dessous.

start <SERVICE>
~~~~~~~~~~~~~~~

Cette commande permet de lancer n'importe quel service de l'application dans le container (``ops``, ``www``, *etc*).

cron
~~~~

Lance un démon *cron* en avant-plan, la *crontab* de l'application est chargée automatiquement avant le lancement du
démon.

[<commande> [<args>]]
~~~~~~~~~~~~~~~~~~~~~

Lance le script, la commande ou un *shell* dans le conteneur. Dans tous les cas, l'environnement propre au lancement de
l'application est mis en place (activation du *venv* *Python*, mise en place des variables d'environnement de
l'application, ...)

- Si l'image est lancée sans argument, un *shell* (``bash``) sera lancé.
- Si il existe un fichier dans le dossier ``/scripts`` (qui doit donc être monté dans le container) qui à le même nom
  que la commande alors celui-ci sera appelé. Dans ce cas, ce script *doit* commencer par un *shebang* classique
  (par exemple ``#!/usr/bin/bash`` ou ``#!/usr/bin/env python``).
- Dans les autres cas la commande sera lancée.

Par exemple, les migrations de *Django* se lancent de la façon suivante :

.. code-block:: bash

    $ docker run \
        -v ${CONFIG_DIR}:/config:ro \
        -v ${MEDIA_DIR}:/media:rw \
        -v ${SCRIPT_DIR}:/scripts:rw \
        -v /dev/log:dev/log:rw \
        -ti \
        ${IMAGE} \
        django-admin.py migrate

Comment lancer un service ?
---------------------------

.. code-block:: bash

    $ docker run \
        -v ${CONFIG_DIR}:/config:ro \
        -v ${SSH_DIR}:/config/ssh-dir:ro \
        -v ${MEDIA_DIR}:/media:rw \
        -v ${SCRIPT_DIR}:/scripts:rw \
        -v /dev/log:dev/log:rw \
        -p ${PORT}:8080 \
        -p ${SUPERVISION_PORT}:8081 \
        -ti \
        ${IMAGE} \
        start ${SERVICE}

.. note::

  Le flag '-ti' ci-dessus n'est la plupart du temps pas nécessaire au lancement d'un service;
  il permet surtout d'interagir (avec un flux stdin) avec la machine virtualisée.


.. _run-scripts:

Comment lancer un script ?
--------------------------

Pour lancer un script, il faut monter le dossier contenant le script et ses dépendances sur une nouvelle instance de
l'image. Ce script doit créer tous ses fichiers de sortie de le dossier courant (``/script`` en l'occurrence).

Le dossier monté dans l'instance doit être inscriptible pour l'utilisateur utilisé dans l'instance (*blue*, *UID* 1000 ;
**Faire un** ``sudo chown -R 1000`` **ou un** ``chmod -R go+rwX`` **sur le dossier**).

Le script se lance ensuite de la façon suivante

.. code-block:: bash

    $ chmod go+rwX ${SCRIPT_DIR}
    $ chmod -R go+rX ${SCRIPT_DIR}
    $ docker run \
        -v ${CONFIG_DIR}:/config:ro \
        -v ${MEDIA_DIR}:/media:rw \
        -v ${SCRIPT_DIR}:/scripts:rw \
        -v /dev/log:dev/log:rw \
        -ti \
        ${IMAGE} \
        ${SCRIPT_NAME} ${SCRIPT_ARGS}


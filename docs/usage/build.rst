Création d'une image
====================

Comment créer une image ?
-------------------------

.. note:: **Prérequis**

  Pour pouvoir lancer la commande ``docker`` sans droits super-utilisateur, sous Debian

  .. code-block:: bash

      $ sudo adduser $(whoami) docker
      $ su $(whoami)  # pour recharger les groupes


La création d'une image se fait via la commande ``grocker.py``

.. code-block:: bash

    $ grocker.py --python {2.7,3.4} {project}=={version}
    $ # par exemple pour créer une image de dev de milborne :
    $ grocker.py --python 2.7 milborne==0.4.0.dev2015041600283
    $ # ou en utilisant le Makefile
    $ make build PACKAGE=milborne VERSION=0.4.0.dev2015041600283 PYTHON_VERSION=2.7

Les paquets *Python* sont récupérés en utilisant la configuration *pip* de la machine hôte.


Autres commandes utiles
-----------------------

Il est possible de nettoyer l'environnement de construction en lançant la commande ``make clean`` et de supprimer les
images déjà construites avec la commande ``make purge``.

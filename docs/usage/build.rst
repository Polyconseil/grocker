Création d'une image
====================

Comment créer une image ?
-------------------------

.. note:: **Prérequis**

  Pour pouvoir lancer la commande ``docker`` sans droits super-utilisateur, sous Debian

  .. code-block:: bash

      $ sudo adduser $(whoami) docker
      $ su $(whoami)  # pour recharger les groupes


La création d'une image se fait via la commande ``grocker``

.. code-block:: bash

    $ grocker {python2, python3} --entry-point {grocker-pyapp, grocker-bluedjango} build {project}=={version}
    $ # par exemple pour créer une image de dev de milborne :
    $ grocker --runtime python2 --entry-point grocker-bluedjango build milborne==0.4.0.dev2015041600283

Les paquets *Python* sont récupérés en utilisant la configuration *pip* de la machine hôte.

.. note:: **Attention**

   Si vous refaite une image docker d'une version releasée d'un SI, prenenez garde à utiliser l'option ``--pip-constraint``:
   $ grocker --runtime python2 --entry-point grocker-bluedjango build milborne==0.4.0.dev2015041600283 --pip-constraint release.txt




Autres commandes utiles
-----------------------

Il est possible de nettoyer l'environnement de construction en lançant la commande ``make clean`` et de supprimer les
images déjà construites avec la commande ``grocker --purge all``.

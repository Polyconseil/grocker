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

    $ grocker {python2, python3} build {project}=={version}
    $ # par exemple pour créer une image de dev de milborne :
    $ grocker --runtime python2 build milborne==0.4.0.dev2015041600283

Les paquets *Python* sont récupérés en utilisant la configuration *pip* de la machine hôte.


Autres commandes utiles
-----------------------

Il est possible de nettoyer l'environnement de construction en lançant la commande ``make clean`` et de supprimer les
images déjà construites avec la commande ``grocker --purge all``.


Fichier de configuration "projet"
---------------------------------

Il est possible d'ajouter un fichier ``.grocker.yml`` à la racine de l'environnement de construction pour configurer le projet à construire.
Ce fichier suit la syntax YAML et contient trois entrées :

    :runtime: le runtime à utiliser
    :dependencies: la liste des dépendances.

Chaque entrée de la liste de dépendances peut-être selon le cas :

   - ``my-dependency``,  pour les dépendances d'exécution sans dépendance de construction,
   - ``my-dependency: my-dependency-dev``, pour les dépendances ayant une dépendance de construction,
   - ``my-dependency: [my-dependency-dev, my-dependency-dev2]``, pour les dépendances ayant plusieurs dépendances de construction.

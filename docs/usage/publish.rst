Publication des images
======================

Publication
-----------

Pour publier une image sur le registre docker, il suffit de lancer la commande suivante :

.. code-block:: bash

    $ docker push ${IMAGE}:${VERSION}


La liste des versions des images publiées est récupérable sur l'url suivante :
https://(registry_fqdn)/v2/(app)/tags/list


Récupération
------------

.. code-block:: bash

  $ docker pull ${IMAGE}:${VERSION}

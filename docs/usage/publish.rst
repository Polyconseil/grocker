Publication des images
======================

Docker registry
---------------

Polyconseil docker's registry is accessible at ``docker.polydev.blue``.

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

  $ docker pull (registry_fqdn)/${IMAGE}:${VERSION}


Réplication
-----------

Pour créer une image mirroir d'une image officielle sur le registry
Polyconseil, choisir l'image à répliquer à l'aide de:

.. code:: shell

    $ docker images

Tagger l'image:

.. code:: shell

    $ docker tag ${IMAGE_ID} ${registry_fqdn}/${IMAGE}:${VERSION}

La publier sur le registry:

.. code:: shell

    $ docker push ${registry_fqdn}/${IMAGE}:${VERSION}


SHA256 d'une Image
------------------

Vous pouvez à tout moment récupérer le SHA256 d'une image poussée sur notre registry avec::

.. code:: shell

    $ curl -X GET -I https://docker.polydev.blue/v2/<PROJECT>/manifests/<VERSION> | grep Docker-Content-Digest

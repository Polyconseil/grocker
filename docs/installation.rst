Installation
============

Grocker nécessite `docker`_ pour pouvoir être utilisé.

.. _docker: https://www.docker.com/

Debian
------

  sudo apt-get update
  sudo apt-get install apt-transport-https ca-certificates
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
  sudo sh -c "echo 'deb https://get.docker.com/ubuntu docker main' > /etc/apt/sources.list.d/docker"
  sudo apt-get update
  sudo apt-get install lxc-docker
  sudo addgroup $USER docker
  sudo service docker restart

.. note::

  Docker might take route `172.17.0.1/some_some` on installation which conflicts
  with ops.blue-city.co.uk (ip 172.17.57.12) preventing its access.
  You can tell Docker to install itself somewhere else by adding
  `DOCKER_OPTS="--bip=10.1.1.1/24"` in file */etc/default/docker* then
  restart your computer (`sudo service docker restart` is not sufficient).

OSX
---

Installer `Boot2Docker`_ puis:

  - Initialiser la VM (une seule fois après installation)::

    boot2docker init

  - Pour démarrer la VM et le démon Docker::

    boot2docker start
    eval "$(boot2docker shellinit)"

.. _Boot2Docker: http://boot2docker.io

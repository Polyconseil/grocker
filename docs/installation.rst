Installation
============

Grocker nécessite `docker`_ pour pouvoir être utilisé.

Sur un système Debian::

  sudo apt-get update
  sudo apt-get install apt-transport-https ca-certificates
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
  sudo sh -c "echo 'deb https://get.docker.com/ubuntu docker main' > /etc/apt/sources.list.d/docker"
  sudo apt-get install lxc-docker
  sudo addgroup $USER docker
  sudo service docker restart

.. _docker: https://www.docker.com/

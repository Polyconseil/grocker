Installation
============

*Grocker* require `Docker <https://www.docker.com/>`_ to work.


Debian
------

.. code-block:: shell

  sudo apt update
  sudo apt install apt-transport-https ca-certificates
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
  sudo sh -c "echo 'deb https://apt.dockerproject.org/repo debian-jessie main' > /etc/apt/sources.list.d/docker.list"
  sudo apt update
  sudo apt install docker-engine
  sudo addgroup $USER docker

The *docker-engine package* (v1.6) has a bug within its *systemd* init file which prevent to load docker options see
:ref:`polyconseil_docker_bridge`.

Mac OS X
--------

.. warning::

    *boot2docker* is deprecated, use *Docker Toolbox* instead.

*Docker Toolbox* is an all-in-one installer which make coffee: https://www.docker.com/docker-toolbox

It will install Docker and other tools as *Docker Machine* or *Kitematic*.


Archlinux
---------

First, install docker and add yourself to the docker group.

.. code-block:: shell

    sudo pacman -S docker
    sudo gpasswd -a $USER docker

.. note::

    You may have to logout/login or ``su - $USER`` in your shell so that the new group is added to your user.


.. _polyconseil_docker_bridge:

Unable to access `blue city <https://ops.blue-city.co.uk>`_
-----------------------------------------------------------

Docker usually takes route ``172.17.0.1/some_some`` on installation, which conflicts with
`https://ops.blue-city.co.uk/ <https://ops.blue-city.co.uk>`_ (ip ``172.17.57.12``), preventing access to this
resource.

Linux
"""""

A proper solution is to override the default service file for docker to specify
another network bridge then restarting the docker daemon. As **root**:

.. code-block:: bash

    $ mkdir /etc/systemd/system/docker.service.d/
    $ cat <<EOF > /etc/systemd/system/docker.service.d/polyconseil_bridge.conf
    [Unit]
    Description=Docker Application Container Engine for Polyconseil (bridge network changed)

    [Service]
    ExecStart=
    ExecStart=/usr/bin/docker -d -H fd:// --bip=10.1.1.1/24
    EOF
    $ systemctl restart docker.service

.. note::

    You have to put the blank ``ExecStart=`` line in to ensure that directive
    gets overridden.

    For more information, ``man 5 systemd.service`` -> ExecStart=. "If the
    empty string is assigned to this option, the list of commands to start is
    reset, prior assignments of this option will have no effect."

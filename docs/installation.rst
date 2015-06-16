Installation
============

Grocker nécessite `docker`_ pour pouvoir être utilisé.

.. _docker: https://www.docker.com/

Debian
------

.. code-block:: shell

  sudo apt-get update
  sudo apt-get install apt-transport-https ca-certificates
  sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
  sudo sh -c "echo 'deb https://get.docker.com/ubuntu docker main' > /etc/apt/sources.list.d/docker.list"
  sudo apt-get update
  sudo apt-get install lxc-docker
  sudo addgroup $USER docker
  sudo service docker restart

The lxc-docker package (v1.6) has a bug within its systemd init file which prevent to load docker options.
Edit the docker's systemd file **/lib/systemd/system/docker.service** and these line after the **[service]** section:

.. code-block:: shell

  [Service]
  EnvironmentFile=/etc/default/docker
  ExecStart=/usr/bin/docker -d -H fd:// $DOCKER_OPTS

Then reload the systemd configuration

.. code-block:: shell

  systemctl daemon-reload

.. note::

  Docker might take route ``172.17.0.1/some_some`` on installation which conflicts
  with ops.blue-city.co.uk (ip 172.17.57.12) preventing its access.
  You can tell Docker to install itself somewhere else by adding
  ``DOCKER_OPTS="--bip=10.1.1.1/24"`` in file */etc/default/docker*.

  **NB: The docker bridge IP must be a valid IP address in the CIDR notation, and not a network adress.**

.. code-block:: shell

  service docker stop
  ip link del docker0 && iptables -t nat -F
  service docker start

OSX
---

Installer `Boot2Docker`_ puis:

  - Initialiser la VM (une seule fois après installation):

    .. code-block:: shell

      boot2docker init

  - Pour démarrer la VM et le démon Docker:

    .. code-block:: shell

      boot2docker start
      eval "$(boot2docker shellinit)"

.. _Boot2Docker: http://boot2docker.io


Archlinux
---------

First, install docker and add yourself to the docker group.

.. code-block:: shell

    sudo pacman -S docker
    sudo gpasswd -a $USER docker

.. note::

    You may have to logout/login or ``su - $USER`` in your shell so that the new group is added to your user.

Unable to access `blue city <https://ops.blue-city.co.uk>`_
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Docker usually takes route ``172.17.0.1/some_some`` on installation, which conflicts with
`https://ops.blue-city.co.uk/ <https://ops.blue-city.co.uk>`_ (ip ``172.17.57.12``), preventing access to this
resource.

A proper solution would be to override the default service file for docker to specify another network bridge. To do so,
run the following commands as **root**:

.. code-block:: shell

    mkdir /etc/systemd/system/docker.service.d/
    cp /usr/lib/systemd/system/docker.service /etc/systemd/system/docker.service.d/docker_poly.conf

Edit the new configuration with your favorite text editor (``/etc/systemd/system/docker.service.d/docker_poly.conf``)
to add ``--bip=10.1.1.1/24`` to the ExecStart parameter and perhaps modify the Description parameter. It should look
like:

.. code-block:: ini

    [Unit]
    Description=Docker Application Container Engine for Polyconseil (DNS updated)
    Documentation=http://docs.docker.com
    After=network.target docker.socket
    Requires=docker.socket

    [Service]
    ExecStart=
    ExecStart=/usr/bin/docker -d -H fd:// --bip=10.1.1.1/24
    MountFlags=slave
    LimitNOFILE=1048576
    LimitNPROC=1048576
    LimitCORE=infinity

    [Install]
    WantedBy=multi-user.target

.. note::

    You have to put the blank ``ExecStart=`` line in to ensure that directive gets overridden.

You should restart the docker daemon.

.. code-block:: shell

    systemctl restart docker.service

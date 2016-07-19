Troubleshooting
===============

I have a `PermissionError: [Errno 13] Permission denied`
--------------------------------------------------------

Grocker does not ask for superuser rights before invoking Docker. The Docker socket has to be
readable and writable by the current user. Many distributions create this socket to be readable
and writable by *root* and the *docker* group.

One way to be able to use Grocker is to add your user to the *docker* group. On Debian:

.. code-block:: bash

      $ sudo adduser $(whoami) docker
      $ su $(whoami)  # reload groups, you should also restart your session

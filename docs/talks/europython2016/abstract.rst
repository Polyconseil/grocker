Grocker, a Docker build chain for Python applications
=====================================================

Short Abstract
--------------

Grocker is a Docker build chain for Python. It transforms your Python package
into a self-contained Docker image which can be easily deployed in a Docker
infrastructure. Grocker also adds a Docker entry point to easily start your
application.

Abstract
--------

At Polyconseil, we build Paris electric car-sharing service: Autolib'. This
system is based on many services developed using web technologies, Django
and our own libraries to handle business logic.

Packaging is already a difficult problem, deploying large Python projects is
even more difficult. When deploying on a live and user-centric system like
Autolib', you cannot rely on Pip and external PyPI servers which might become
unavailable and are beyond your control. In the beginning we used classic
Debian packaging: it was a maintenance hell. It took hours to build our
packages and update their metadata to match our Python packages. So we
switched to Docker.

Docker allows us to have a unique item that is deployed in production systems:
code updates are now atomic and deterministic! But before deploying the Docker
image, you need to build it. That's where Grocker comes in.

Grocker is a Docker build chain for Python. It will transform your Python
package into a self-contained Docker image which can be easily deployed in a
Docker Infrastructure. Grocker also adds a Docker entry point to easily start
your application.

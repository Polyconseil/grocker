FROM debian:jessie
ENV LANG C.UTF-8
# configure debian to bother us with apt things and to be lighter
ADD ./configure_apt.sh /tmp/configure_apt.sh
RUN /tmp/configure_apt.sh
RUN DEBIAN_FRONTEND=noninteractive apt-get update
ADD ./provision.sh /tmp/provision.sh
RUN /tmp/provision.sh

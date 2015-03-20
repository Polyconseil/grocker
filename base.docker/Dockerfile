FROM debian:jessie
ENV LANG C.UTF-8
RUN DEBIAN_FRONTEND=noninteractive apt-get update
ADD ./provision.sh /tmp/provision.sh
RUN /tmp/provision.sh

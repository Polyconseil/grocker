FROM debian:jessie

ENV LANG C.UTF-8

# Configure apt for a lighter & quieter use.
ADD 00_apt_config.sh /tmp/00_apt_config.sh
ADD nginx_signing.key /tmp/nginx_signing.key
RUN /tmp/00_apt_config.sh

# Add a variables file that will be sourced by descendants
ADD base.env /opt/bundle/base.env

# Install required packages, setup base user.
ADD 01_provision.sh /tmp/01_provision.sh
RUN /tmp/01_provision.sh

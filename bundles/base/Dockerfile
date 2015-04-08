FROM debian:jessie

ENV LANG C.UTF-8

# Add a variables file that will be sourced by descendants
ADD base_vars.sh /opt/bundle/base_vars.sh

# Configure apt for a lighter & quieter use.
ADD 00_apt_config.sh /tmp/00_apt_config.sh
RUN /tmp/00_apt_config.sh

# Update the packages, once in the build.
RUN DEBIAN_FRONTEND=noninteractive apt-get update

# Install required packages, setup base user.
ADD 01_provision.sh /tmp/01_provision.sh
RUN /tmp/01_provision.sh

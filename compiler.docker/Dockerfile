FROM bluesolutions/bundle-base:0.1
RUN DEBIAN_FRONTEND=noninteractive apt-get update
ADD provision.sh /tmp/provision.sh
ADD compiler.py /tmp/compiler.py
RUN /tmp/provision.sh

USER blue
ENTRYPOINT ["/home/blue/bin/compiler.py"]

FROM docker.polyconseil.fr/bundle-base:${grocker_version}

# Install system packages and compiler script in final destination
ADD 00_install_python.sh /tmp/00_install_python.sh
ADD 01_compile.py /tmp/01_compile.py
RUN /tmp/00_install_python.sh

# Make the entry point run the compile script
USER blue
ENTRYPOINT ["/home/blue/bin/compile.py"]

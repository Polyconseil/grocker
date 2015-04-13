FROM bluesolutions/bundle-base:0.1

# Run the installer script for target package
ADD 00_install_package.sh /tmp/00_install_package.sh
ADD 02_entrypoint.py /tmp/02_entrypoint.py
ADD templates/ /tmp/templates/
ADD output/ /tmp/output/
RUN /tmp/00_install_package.sh

# Setup cron environment
ADD 01_setup_cron.sh /tmp/01_setup_cron.sh
RUN /tmp/01_setup_cron.sh

# Prepare the image to run the entrypoint
VOLUME [/media /scripts /config /dev/log]
EXPOSE 8080 8081
USER blue
ENTRYPOINT ["/home/blue/app/bin/entrypoint.py"]

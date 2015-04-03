FROM bluesolutions/bundle-base:0.1

ADD provision.sh /tmp/provision.sh
COPY output/* /tmp/output/

RUN /tmp/provision.sh

VOLUME [/media /scripts /config /dev/log]
EXPOSE 8080 8081

USER blue


ENTRYPOINT ["/home/blue/app/bin/entrypoint"]

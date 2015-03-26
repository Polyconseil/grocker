FROM bluesolutions/bundle-base:0.1

ADD provision.sh /tmp/provision.sh
COPY output/* /tmp/output/

RUN /tmp/provision.sh

USER blue


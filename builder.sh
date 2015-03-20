#!/usr/bin/env bash

VERSION=$(cat version.txt)
BLUE_HOME=/home/blue
OUTPUT_DIR=$(pwd)/output

# Build Docker Images
for image in base compiler; do
    # TODO: Update base image version in compiler Dockerfile
    docker build --force-rm=true --rm=true -t bluesolutions/bundle-${image}:${VERSION} ${image}.docker/.
done

# Create Output Directory
if ! [ -e ${OUTPUT_DIR} ]; then
    mkdir ${OUTPUT_DIR}
fi

# Run Compiler
docker run --rm --volume ~/.pip/:${BLUE_HOME}/.pip.host --volume ${OUTPUT_DIR}:${BLUE_HOME}/output bluesolutions/bundle-compiler:${VERSION} "$@"

# TODO: Create Runner Image

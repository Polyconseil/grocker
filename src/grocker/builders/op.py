# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
import logging
import os.path

import docker
import docker.errors
import docker.utils.json_stream

from .. import __version__
from .. import helpers
from .. import six

logger = logging.getLogger(__name__)


def is_prefixed_image(name):
    return '/' in name


@contextlib.contextmanager
def docker_build_context(context_path):
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource(context_path, build_dir)
        yield build_dir


def docker_build_image(docker_client, path, name, role=None, labels=None, **kwargs):
    computed_labels = {
        'grocker.version': __version__,
        'grocker.image.role': role,
    }
    computed_labels.update(labels or {})
    stream = docker_client.api.build(
        path=path,
        tag=name,
        rm=True,
        forcerm=True,
        labels=computed_labels,
        **kwargs
    )
    _inspect_stream(stream)
    try:
        return docker_client.images.get(name)
    except docker.errors.ImageNotFound:
        raise RuntimeError('Image build failed')


def docker_get_or_build_image(docker_client, name, builder):
    try:
        return docker_client.images.get(name)
    except docker.errors.ImageNotFound:
        try:
            return docker_pull_image(docker_client, name)
        except docker.errors.NotFound:
            image = builder(docker_client)
            if is_prefixed_image(name):
                image = docker_push_image(docker_client, name)
            return image


def get_or_create_data_volume(docker_client, name, role, labels=None):
    logger.info('Creating volume %s...')
    computed_labels = {
        'grocker.version': __version__,
        'grocker.image.role': role,
    }
    computed_labels.update(labels or {})
    return docker_client.volumes.create(
        name=name,
        labels=computed_labels,
    )


def docker_pull_image(docker_client, name):
    logger.info('Pulling image %s...', name)
    return docker_client.images.pull(name)


def docker_push_image(docker_client, name):
    logger.info('Pushing image %s...', name)
    docker_client.images.push(name)
    return docker_client.images.get(name)


def docker_run_container(docker_client, name, command, volumes=None, environment=None):
    logger.info(
        'Running %s on image %s (volumes:%s, environment:%s)',
        command, name, volumes, environment,
    )
    container = docker_client.containers.run(
        image=name,
        command=command,
        environment=environment,
        volumes=volumes,
        detach=True,
    )

    stream = container.attach(stream=True, logs=True)
    for line in stream:
        print(line.decode('utf-8'), end='')
    return_code = container.wait()
    container.remove()
    if return_code != 0:
        raise RuntimeError('Container exit with a non-zero return code (%d).', return_code)


def _inspect_stream(stream):
    """Return some data about the stream."""
    error = False
    for line in docker.utils.json_stream.json_stream(stream):
        if 'stream' in line:
            print(line['stream'], end='')
        elif 'error' in line:
            print(line['error'])
            error = True
        else:
            print(line)
    print()
    return not error

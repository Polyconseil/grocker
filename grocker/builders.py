# -*- coding: utf-8 -*-
# Copyright (c) 2011-2015 Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import functools
import json
import logging
import os.path
import shutil
import sys
import uuid

import docker
import docker.utils

from . import __version__, DOCKER_MIN_VERSION
from . import six
from . import helpers


def check_docker_version(docker_client):
    def version2tuple(version):
        return [int(x) for x in version.split('.')]

    logger = logging.getLogger(__name__)
    docker_version = docker_client.version().get('Version', '0')
    need_update = version2tuple(docker_version) < version2tuple(DOCKER_MIN_VERSION)
    if need_update:
        logger.critical('Grocker needs Docker >= %s', DOCKER_MIN_VERSION)
        exit(1)


def build_root_image(docker_client, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/root-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {'version': __version__},
        )
        return docker_build_image(docker_client, build_dir, tag=tag)


def build_compiler_image(docker_client, root_image_tag, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/compiler-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {'root_image_tag': root_image_tag},
        )
        return docker_build_image(docker_client, build_dir, tag=tag)


def build_runner_image(docker_client, root_image_tag, entrypoint, runtime, release, package_dir, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/runner-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {'root_image_tag': root_image_tag},
        )
        helpers.render_template(
            os.path.join(build_dir, '.grocker.j2'),
            os.path.join(build_dir, '.grocker'),
            {
                'grocker_version': __version__,
                'runtime': runtime,
                'entrypoint': entrypoint,
                'release': release,
            },
        )
        shutil.copytree(package_dir, os.path.join(build_dir, 'packages'))
        return docker_build_image(docker_client, build_dir, tag=tag)


def get_root_image(docker_client, docker_registry):
    tag = '{}/grocker-root:{}'.format(docker_registry, __version__)
    return docker_get_or_build_image(docker_client, tag, build_root_image)


def get_compiler_image(docker_client, docker_registry):
    tag = '{}/grocker-compiler:{}'.format(docker_registry, __version__)
    root_tag = get_root_image(docker_client, docker_registry)
    return docker_get_or_build_image(
        docker_client,
        tag,
        functools.partial(build_compiler_image, root_image_tag=root_tag),
    )


def compile_wheels(docker_client, compiler_tag, python, release, entrypoint, package_dir, pip_conf):
    binds = {
        package_dir: {
            'bind': '/home/grocker/packages',
            'mode': 'rw',
        },
        pip_conf: {
            'bind': '/home/grocker/pip.conf',
            'mode': 'ro',
        }
    }
    command = [
        '--pip-conf', '/home/grocker/pip.conf',
        '--package-dir', '/home/grocker/packages',
        '--python', python,
        release, entrypoint,
    ]

    if not os.path.exists(package_dir):
        os.makedirs(package_dir)

    try:
        docker_run_container(docker_client, compiler_tag, command, binds=binds)
    except RuntimeError:
        exit(1)


def docker_get_client():
    return docker.Client(**docker.utils.kwargs_from_env())


def docker_build_image(docker_client, path, tag=None):
    stream = docker_client.build(path=path, tag=tag, rm=True, forcerm=True)
    docker_stream(stream)
    return tag


def docker_stream(stream):
    old_status = None
    for line in (json.loads(x) for x in stream):
        if 'status' in line:
            status = line['status']
            if old_status != status:
                old_status = status
                print()
                print(old_status, end='')
            else:
                print('.', end='')
                sys.stdout.flush()  # Python 2.7 does not support flush argument on print() function.
        elif 'stream' in line:
            print(line['stream'], end='')
        elif 'error' in line:
            print(line['error'])
        else:
            print(line)
    print()


def docker_pull_image(docker_client, name):
    stream = docker_client.pull(name, stream=True)
    docker_stream(stream)

    return [image for image in docker_client.images() if name in image['RepoTags']]


def docker_push_image(docker_client, name):
    stream = docker_client.push(name, stream=True)
    docker_stream(stream)


def docker_get_or_build_image(docker_client, name, builder):
    images = [image for image in docker_client.images() if name in image['RepoTags']]
    if not images:
        images = docker_pull_image(docker_client, name)
    if not images:
        builder(docker_client, tag=name)
        docker_push_image(docker_client, name)
    return name


def docker_run_container(docker_client, tag, command, binds=None):
    container = docker_client.create_container(
        image=tag,
        command=command,
        volumes=[x['bind'] for x in binds.values()] if binds else [],
        host_config=docker.utils.create_host_config(binds=binds),
    )

    container_id = container.get('Id')
    docker_client.start(container_id)
    stream = docker_client.attach(container_id, stream=True, logs=True)
    for line in stream:
        print(line.decode('utf-8'), end='')
    return_code = docker_client.wait(container_id)
    docker_client.remove_container(container_id)
    if return_code != 0:
        raise RuntimeError('Container exit with a non-zero return code (%d).', return_code)


def docker_purge_images(docker_client, filters=()):
    filter_desc = {
        'dangling': {'dangling': True},
        'run': {'label': 'grocker.step=run'},
        'build': {'label': 'grocker.step=build'},
    }

    for filter_name in filters:
        images = docker_client.images(filters=filter_desc[filter_name])
        for image in images:
            print('Purging: {tags} ({img[Id]})'.format(img=image, tags=', '.join(image['RepoTags'])))
            docker_client.remove_image(image)

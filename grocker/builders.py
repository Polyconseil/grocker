# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
import functools
import io
import itertools
import json
import logging
import os.path
import re
import sys
import uuid

import docker
import docker.utils

from . import __version__, DOCKER_MIN_VERSION
from . import six
from . import helpers


DIGEST_RE = re.compile(r'[\w\.-]+: digest: sha256:(\w+) size: \d+')


def is_docker_outdated(docker_client):
    def version2tuple(version):
        return [int(x) for x in version.split('.')]

    logger = logging.getLogger(__name__)
    docker_version = docker_client.version().get('Version', '0')
    need_update = version2tuple(docker_version) < version2tuple(DOCKER_MIN_VERSION)
    if need_update:
        logger.critical('Grocker needs Docker >= %s', DOCKER_MIN_VERSION)

    return need_update


def get_run_dependencies(dependency_list):
    """
    Parse list of dependencies to only get run dependencies.

    Dependency list is a list of string or dict, which match the following
    format:

     [
        'run_dependency_1',
        {'run_dependency_2': 'build_dependency_2'},
        {'run_dependency_3': ['build_dependency_3.1', 'build_dependency_3.2']},
    ]
    """
    for dependency in dependency_list:
        if isinstance(dependency, dict):
            for key in dependency:
                yield key
        else:
            yield dependency


def get_build_dependencies(dependency_list):
    """
    Parse list of dependencies to only get build dependencies

    see get_run_dependencies() for dependency list format
    """
    for dependency in dependency_list:
        if isinstance(dependency, dict):
            for value_or_list in dependency.values():
                if isinstance(value_or_list, list):
                    for value in value_or_list:
                        yield value
                else:
                    yield value_or_list
        else:
            yield dependency


def get_dependencies(config, with_build_dependencies=False):
    runtime_dependencies = config['system']['runtime'][config['runtime']]

    dependencies = itertools.chain(
        config['system']['base'],
        get_run_dependencies(runtime_dependencies),
        get_run_dependencies(config['dependencies'])
    )

    if with_build_dependencies:
        build_dependencies = itertools.chain(
            config['system']['build'],
            get_build_dependencies(runtime_dependencies),
            get_build_dependencies(config['dependencies'])
        )

        dependencies = itertools.chain(dependencies, build_dependencies)

    return list(dependencies)


def build_root_image(docker_client, config, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/root-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {'version': __version__},
        )

        dependencies = get_dependencies(config)
        with io.open(os.path.join(build_dir, 'provision.env'), 'w') as fp:
            fp.write('SYSTEM_DEPS="{}"'.format(' '.join(dependencies)))

        return docker_build_image(docker_client, build_dir, tag=tag)


def build_compiler_image(docker_client, root_image_tag, config, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/compiler-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {'root_image_tag': root_image_tag},
        )

        dependencies = get_dependencies(config, with_build_dependencies=True)
        with io.open(os.path.join(build_dir, 'provision.env'), 'w') as fp:
            fp.write('SYSTEM_DEPS="{}"'.format(' '.join(dependencies)))

        return docker_build_image(docker_client, build_dir, tag=tag)


def build_pypi_image(docker_client, tag):
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/nginx-pypi', build_dir)
        return docker_build_image(docker_client, build_dir, tag=tag)


def get_or_create_data_volume(docker_client, name):
    for volume in docker_client.volumes()['Volumes']:
        if volume['Name'] == name:
            return volume
    return docker_client.create_volume(name=name)


@contextlib.contextmanager
def http_wheel_server(docker_client, wheels_volume_name):
    nginx_image = docker_get_or_build_image(
        docker_client,
        'docker.polydev.blue/grocker-nginx-pypi:1.0.0',
        build_pypi_image,
    )
    nginx = docker_client.create_container(
        image=nginx_image,
        host_config=docker_client.create_host_config(
            binds={
                wheels_volume_name: {
                    'bind': '/wheels',
                    'mode': 'ro',
                }
            },
        ),
    )
    nginx_container_id = nginx.get('Id')
    docker_client.start(nginx_container_id)
    nginx_server_ip = docker_client.inspect_container(nginx_container_id)['NetworkSettings']['IPAddress']

    try:
        yield nginx_server_ip
    finally:
        docker_client.remove_container(nginx_container_id, force=True)


def build_runner_image(
        docker_client, root_image_tag, config, release, wheels_volume_name, pip_constraint=None, tag=None
):
    tag = tag or '{}.grocker'.format(uuid.uuid4())

    with http_wheel_server(docker_client, wheels_volume_name) as docker_ip:
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
                    'runtime': config['runtime'],
                    'entrypoint': config['entrypoint'],
                    'release': release,
                },
            )
            if pip_constraint:
                with io.open(pip_constraint, 'r') as fp:
                    with io.open(os.path.join(build_dir, 'constraints.txt'), 'w') as f:
                        f.write(fp.read())

            with io.open(os.path.join(build_dir, 'pypi.ip'), 'w') as f:
                f.write(docker_ip)

            return docker_build_image(docker_client, build_dir, tag=tag)


def get_root_image(docker_client, config, docker_registry):
    tag = '{registry}/grocker-{runtime}-root:{version}-{hash}'.format(
        registry=docker_registry,
        runtime=config['runtime'],
        version=__version__,
        hash=helpers.hash_list(get_dependencies(config)),
    )
    return docker_get_or_build_image(
        docker_client,
        tag,
        functools.partial(build_root_image, config=config),
    )


def get_compiler_image(docker_client, config, docker_registry):
    tag = '{registry}/grocker-{runtime}-compiler:{version}-{hash}'.format(
        registry=docker_registry,
        runtime=config['runtime'],
        version=__version__,
        hash=helpers.hash_list(get_dependencies(config)),
    )
    root_tag = get_root_image(docker_client, config, docker_registry)
    return docker_get_or_build_image(
        docker_client,
        tag,
        functools.partial(build_compiler_image, config=config, root_image_tag=root_tag),
    )


def get_pip_env(pip_conf):
    logger = logging.getLogger(__name__)

    def get(cfg, section, option, default=None):
        try:
            return cfg.get(section, option)
        except (six.configparser.NoSectionError, six.configparser.NoOptionError):
            return default

    if not pip_conf:
        return {}

    logger.info('-> Pip use configuration from %s.', pip_conf)
    config = six.configparser.ConfigParser()
    config.read(pip_conf)

    env = {
        'PIP_INDEX_URL': get(config, 'global', 'index-url'),
        'PIP_EXTRA_INDEX_URL': get(config, 'global', 'extra-index-url'),
    }
    env = {k: v for k, v in env.items() if v}
    logger.debug('pip using env: %s', env)
    return env


def compile_wheels(docker_client, compiler_tag, config, release, wheels_volume_name, pip_conf, pip_constraint):
    wheels_destination_volume = get_or_create_data_volume(docker_client, wheels_volume_name)
    binds = {
        wheels_destination_volume['Name']: {
            'bind': '/home/grocker/packages',
            'mode': 'rw',
        },
    }

    command = [
        '--python', config['runtime'],
        release, config['entrypoint'],
    ]

    if pip_constraint:
        binds[pip_constraint] = {
            'bind': '/home/grocker/constraints.txt',
            'mode': 'ro',
        }
        command = ['--pip-constraint', '/home/grocker/constraints.txt'] + command

    docker_run_container(docker_client, compiler_tag, command, binds=binds, environment=get_pip_env(pip_conf))


def docker_get_client():
    # XXX: hack around docker-machine certificate issue https://github.com/docker/docker-py/issues/731
    extra_kwargs = {'assert_hostname': False} if 'DOCKER_MACHINE_NAME' in os.environ else {}
    return docker.Client(**docker.utils.kwargs_from_env(**extra_kwargs))


def docker_build_image(docker_client, path, tag=None):
    stream = docker_client.build(path=path, tag=tag, rm=True, forcerm=True, pull=True)
    data = inspect_stream(stream)
    if not data['success']:
        raise RuntimeError('Image build failed')
    return tag


def inspect_stream(stream):
    """Return some data about the stream."""
    old_status = None
    data = {'success': True}
    for line in (json.loads(six.smart_text(x)) for x in stream):
        if 'status' in line:
            status = line['status']
            match = DIGEST_RE.match(status)
            if match:
                data['sha256'] = match.group(1)
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
            data['success'] = False
        else:
            print(line)
    print()
    return data


def docker_pull_image(docker_client, name):
    logger = logging.getLogger(__name__)
    logger.info('Pulling %s...', name)

    stream = docker_client.pull(name, stream=True)
    inspect_stream(stream)
    return [image for image in docker_client.images() if name in image['RepoTags']]


def docker_push_image(docker_client, name):
    logger = logging.getLogger(__name__)
    logger.info('Pushing %s...', name)

    stream = docker_client.push(name, stream=True)
    data = inspect_stream(stream)
    return data['sha256']


def docker_get_or_build_image(docker_client, name, builder):
    images = [image for image in docker_client.images() if name in image['RepoTags']]
    if not images:
        images = docker_pull_image(docker_client, name)
    if not images:
        builder(docker_client, tag=name)
        docker_push_image(docker_client, name)
    return name


def docker_run_container(docker_client, tag, command, binds=None, environment=None):
    container = docker_client.create_container(
        image=tag,
        command=command,
        environment=environment,
        volumes=[x['bind'] for x in binds.values()] if binds else [],
        host_config=docker_client.create_host_config(binds=binds),
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


def docker_purge_volumes(docker_client, filters=()):
    """Removes dangling volumes (volumes not referenced by any container).

    Args:
        docker_client: a docker-py Client.
        filters: see PurgeAction for choices.

    If ``build`` is in filters, all dangling volumes are deleted.
    If ``dangling`` is the *only* item of filters, the named volumes used by
    grocker as a cache are preserved.
    """
    if 'build' in filters or 'dangling' in filters:
        dangling_volumes = docker_client.volumes(filters={'dangling': True})['Volumes']
        if filters == ['dangling']:
            # Exclude wheels volumes that acts as a grocker cache
            volumes = []
            for volume in dangling_volumes:
                if 'grocker-wheels-cache' not in volume['Name']:
                    # Non grocker data volume => clean it.
                    volumes.append(volume)
                else:
                    # grocker data volume, clean it if outdated.
                    volume_grocker_version = volume['Name'].split('-')[3]
                    if __version__ < volume_grocker_version:
                        volumes.append(volume)
            dangling_volumes = volumes
        for volume in dangling_volumes:
            print('Purging volume: {name}'.format(name=volume['Name']))
            try:
                docker_client.remove_volume(volume['Name'])
            except docker.errors.APIError:
                logging.getLogger(__name__).error("Could not remove volume %s, skipping.", volume['Name'])


def docker_purge_images(docker_client, filters=()):
    filter_desc = {
        'dangling': {'dangling': True},
        'run': {'label': 'grocker.step=run'},
        'build': {'label': 'grocker.step=build'},
    }

    for filter_name in filters:
        images = docker_client.images(filters=filter_desc[filter_name])
        for image in images:
            print('Purging image: {tags} ({img[Id]})'.format(img=image, tags=', '.join(image['RepoTags'])))
            docker_client.remove_image(image)

# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
import functools
import io
import json
import logging
import os.path
import re
import sys
import uuid

import docker
import docker.errors
import docker.utils

from . import __version__, DOCKER_API_VERSION
from . import six
from . import helpers


DIGEST_RE = re.compile(r'[\w\.-]+: digest: (sha256:\w+) size: \d+')


def build_root_image(docker_client, config, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/root-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {
                'version': __version__,
                'runtime': config['runtime'],
            },
        )

        helpers.render_template(
            os.path.join(build_dir, 'apt-repositories.sh.j2'),
            os.path.join(build_dir, 'apt-repositories.sh'),
            {'repositories': config['repositories']},
        )

        dependencies = helpers.get_dependencies(config)
        build_env = {'SYSTEM_DEPS': ' '.join(dependencies)}
        return docker_build_image(docker_client, build_dir, tag=tag, buildargs=build_env)


def build_compiler_image(docker_client, root_image_tag, config, tag=None):
    tag = tag or '{}.grocker'.format(uuid.uuid4())
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/compiler-image', build_dir)
        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            {
                'root_image_tag': root_image_tag,
                'runtime': config['runtime'],
            },
        )

        dependencies = helpers.get_dependencies(config, with_build_dependencies=True)
        with io.open(os.path.join(build_dir, 'provision.env'), 'w') as fp:
            fp.write('SYSTEM_DEPS="{}"'.format(' '.join(dependencies)))

        return docker_build_image(
            docker_client,
            build_dir,
            tag=tag,
            pull=bool(config['docker_image_prefix']),
        )


def build_pypi_image(docker_client, tag):
    with six.TemporaryDirectory() as tmp_dir:
        build_dir = os.path.join(tmp_dir, 'build')
        helpers.copy_resource('resources/docker/nginx-pypi', build_dir)
        return docker_build_image(docker_client, build_dir, tag=tag)


def get_or_create_data_volume(docker_client, name):
    volumes = docker_client.volumes()['Volumes'] or ()
    for volume in volumes:
        if volume['Name'] == name:
            return volume
    return docker_client.create_volume(name=name)


@contextlib.contextmanager
def http_wheel_server(docker_client, wheels_volume_name, config):
    nginx_image = docker_get_or_build_image(
        docker_client,
        config['docker_image_prefix'],
        'grocker-nginx-pypi:1.0.0',
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
        remove_container = helpers.retry(docker.errors.APIError)(docker_client.remove_container)
        remove_container(nginx_container_id, force=True)


def build_runner_image(
        docker_client, root_image_tag, config, release, wheels_volume_name, tag=None
):
    tag = tag or '{}.grocker'.format(uuid.uuid4())

    with http_wheel_server(docker_client, wheels_volume_name, config) as pypi_ip:
        app_name, app_version = release.split('==')
        with six.TemporaryDirectory() as tmp_dir:
            build_dir = os.path.join(tmp_dir, 'build')
            helpers.copy_resource('resources/docker/runner-image', build_dir)
            helpers.render_template(
                os.path.join(build_dir, 'Dockerfile.j2'),
                os.path.join(build_dir, 'Dockerfile'),
                {
                    'root_image_tag': root_image_tag,
                    'entrypoint_name': config['entrypoint_name'],
                    'app_name': app_name,
                    'app_version': app_version,
                    'volumes': config['volumes'],
                    'ports': config['ports'],
                },
            )

            # TODO(fbochu): .grocker file will be obsolete in next major version, so drop it.
            helpers.render_template(
                os.path.join(build_dir, '.grocker.j2'),
                os.path.join(build_dir, '.grocker'),
                {
                    'grocker_version': __version__,
                    'runtime': config['runtime'],
                    'release': release,
                },
            )

            if config['pip_constraint']:
                with io.open(config['pip_constraint'], 'r') as fp:
                    with io.open(os.path.join(build_dir, 'constraints.txt'), 'w') as f:
                        f.write(fp.read())

            return docker_build_image(
                docker_client,
                build_dir,
                tag=tag,
                pull=bool(config['docker_image_prefix']),
                buildargs={'GROCKER_PYPI_IP': pypi_ip},
            )


def get_root_image(docker_client, config):
    img_name = 'grocker-{runtime}-root:{version}-{hash}'.format(
        runtime=config['runtime'],
        version=__version__,
        hash=helpers.config_identifier(config),
    )
    return docker_get_or_build_image(
        docker_client,
        config['docker_image_prefix'],
        img_name,
        functools.partial(build_root_image, config=config),
    )


def get_compiler_image(docker_client, config):
    img_name = 'grocker-{runtime}-compiler:{version}-{hash}'.format(
        runtime=config['runtime'],
        version=__version__,
        hash=helpers.config_identifier(config),
    )
    root_tag = get_root_image(docker_client, config)
    return docker_get_or_build_image(
        docker_client,
        config['docker_image_prefix'],
        img_name,
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


def compile_wheels(docker_client, compiler_tag, config, release, wheels_volume_name, pip_conf):
    wheels_destination_volume = get_or_create_data_volume(docker_client, wheels_volume_name)
    binds = {
        wheels_destination_volume['Name']: {
            'bind': '/home/grocker/packages',
            'mode': 'rw',
        },
    }

    command = ['--python', config['runtime'], release]

    if config['pip_constraint']:
        binds[os.path.abspath(config['pip_constraint'])] = {
            'bind': '/home/grocker/constraints.txt',
            'mode': 'ro',
        }
        command = ['--pip-constraint', '/home/grocker/constraints.txt'] + command

    docker_run_container(docker_client, compiler_tag, command, binds=binds, environment=get_pip_env(pip_conf))


def docker_get_client(**kwargs):
    # XXX: hack around docker-machine certificate issue https://github.com/docker/docker-py/issues/731
    extra_kwargs = {'assert_hostname': False} if 'DOCKER_MACHINE_NAME' in os.environ else {}
    all_extra_kwargs = docker.utils.kwargs_from_env(**extra_kwargs)
    all_extra_kwargs.update(kwargs)
    all_extra_kwargs['version'] = DOCKER_API_VERSION
    client = docker.Client(**all_extra_kwargs)
    client.version()  # Call the API, this will raise if API version is not compatible.
    return client


def docker_build_image(docker_client, path, tag=None, pull=True, buildargs=None):
    stream = docker_client.build(path=path, tag=tag, rm=True, forcerm=True, pull=pull, buildargs=buildargs)
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
                data['hash'] = match.group(1)
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
    return [image for image in docker_client.images() if name in (image['RepoTags'] or [])]


def docker_push_image(docker_client, name):
    logger = logging.getLogger(__name__)
    logger.info('Pushing %s...', name)

    stream = docker_client.push(name, stream=True)
    data = inspect_stream(stream)
    return data['hash']


def docker_get_or_build_image(docker_client, prefix, name, builder):
    full_name = '/'.join((prefix, name)) if prefix else name
    images = [image for image in docker_client.images() if full_name in (image['RepoTags'] or [])]
    if not images and prefix:
        images = docker_pull_image(docker_client, full_name)
    if not images:
        builder(docker_client, tag=full_name)
        if prefix:
            docker_push_image(docker_client, full_name)
    return full_name


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
    """Remove dangling volumes (volumes not referenced by any container).

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
        'runners': {'label': 'grocker.image.kind=runner'},
        'builders': {'label': 'grocker.image.kind=builder'},
    }

    for filter_name in filters:
        images = docker_client.images(filters=filter_desc[filter_name])
        for image in images:
            print('Purging image: {tags} ({img[Id]})'.format(img=image, tags=', '.join(image['RepoTags'])))
            docker_client.remove_image(image)

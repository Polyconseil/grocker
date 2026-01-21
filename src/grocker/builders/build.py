# Copyright (c) Polyconseil SAS. All rights reserved.

import contextlib
import logging
import os.path
import shutil

import docker.errors

from .. import __version__
from .. import helpers
from .. import utils
from . import naming
from . import op

logger = logging.getLogger(__name__)


def build_root_image(docker_client, config):
    with op.docker_build_context('grocker.resources.docker.root-image') as build_dir:
        cfg = config['runtimes'][config['runtime']]
        context = {
            'base_image': cfg['image'],
            'repositories': config['repositories'],
            'runtime': cfg['runtime'],
            'grocker_version': __version__,
        }

        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            context,
        )

        # XXX: We should replace template by env vars
        helpers.render_template(
            os.path.join(build_dir, 'provision.sh.j2'),
            os.path.join(build_dir, 'provision.sh'),
            context,
        )

        dependencies = utils.get_dependencies(config)
        build_env = {
            'SYSTEM_DEPENDENCIES': ' '.join(dependencies),
        }
        return op.docker_build_image(
            docker_client,
            build_dir,
            naming.image_name(config, 'root'),
            buildargs=build_env,
            role='root',
        )


def build_compiler_image(docker_client, config):
    with op.docker_build_context('grocker.resources.docker.compiler-image') as build_dir:
        context = {
            'base_image': naming.image_name(config, 'root'),
            'runtime': config['runtimes'][config['runtime']]['runtime'],
        }

        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            context,
        )

        dependencies = utils.get_dependencies(config, with_build_dependencies=True)
        build_env = {
            'SYSTEM_DEPENDENCIES': ' '.join(dependencies),
        }
        return op.docker_build_image(
            docker_client,
            build_dir,
            naming.image_name(config, 'compiler'),
            buildargs=build_env,
            role='compiler',
        )


def build_wheel_server_image(docker_client, config):
    with op.docker_build_context('grocker.resources.docker.wheel-server') as build_dir:
        return op.docker_build_image(
            docker_client,
            build_dir,
            naming.image_name(config, 'wheel-server'),
            role='wheel-server',
        )


def build_runner_image(docker_client, config, name, requirement):
    # Markers would not make much sense here and url are unsupported.
    with op.docker_build_context('grocker.resources.docker.runner-image') as build_dir:
        context = {
            'base_image': naming.image_name(config, 'root'),
            'entrypoint_name': config['entrypoint_name'],
            'app_name': requirement.project_name,
            'app_extras': ','.join(sorted(requirement.extras)),
            'app_version': requirement.version,
            'volumes': config['volumes'],
            'ports': config['ports'],
            'envs': config['envs'],
        }

        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            context,
        )

        if config.get('pip_constraint'):
            shutil.copyfile(
                config['pip_constraint'],
                os.path.join(build_dir, 'constraints.txt'),
            )

        with wheel_server(docker_client, config) as wheel_server_ip:
            build_env = {
                'GROCKER_WHEEL_SERVER_IP': wheel_server_ip,
            }
            return op.docker_build_image(
                docker_client,
                build_dir,
                name,
                role='runner',
                buildargs=build_env,
                nocache=True,
            )


@contextlib.contextmanager
def wheel_server(docker_client, config):
    image = op.docker_get_or_build_image(
        docker_client,
        naming.image_name(config, 'wheel-server'),
        lambda client: build_wheel_server_image(client, config),
    )

    container = docker_client.containers.run(
        image=image.id,
        volumes={
            naming.wheel_volume_name(config): {
                'bind': '/wheels',
                'mode': 'ro',
            },
        },
        detach=True,
    )
    logger.info('Starting http server in container: %s', container.id)
    container.reload()
    network_settings = container.attrs['NetworkSettings']
    if 'IPAddress' in network_settings:
        # older version of dockerd, dunno exactly which
        server_ip = network_settings['IPAddress']
        logger.debug('http server running with ip: %s', server_ip)
    else:
        # hopefully, there's only one network defined (e.g. 'bridge') so let's try and use that one
        # if there are more, let's hope that the first one that comes up is the one we care about
        network_names = list(network_settings['Networks'])
        first_network_name, *other_network_names = network_names
        server_ip = network_settings['Networks'][first_network_name]['IPAddress']
        logger.debug('http server running with ip: %s (on network %s)', server_ip, first_network_name)
        if other_network_names:
            logger.debug('(ignored networks: %s)', ', '.join(other_network_names))

    try:
        yield server_ip
    finally:
        helpers.retry(docker.errors.APIError)(container.remove)(force=True)

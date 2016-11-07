# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import contextlib
import logging
import os.path
import shutil

import docker.errors
from packaging import requirements

from .. import __version__
from .. import helpers
from .. import utils
from . import op
from . import naming

logger = logging.getLogger(__name__)


def should_pull(config):
    return bool(config['docker_image_prefix'])


def build_root_image(docker_client, config):
    with op.docker_build_context('resources/docker/root-image') as build_dir:
        context = {
            'base_image': config['system']['image'],
            'repositories': config['repositories'],
            'runtime': config['runtime'],
            'grocker_version': __version__,
        }

        helpers.render_template(
            os.path.join(build_dir, 'Dockerfile.j2'),
            os.path.join(build_dir, 'Dockerfile'),
            context,
        )

        # FIXME(fbochu): Replace template by env vars
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
    with op.docker_build_context('resources/docker/compiler-image') as build_dir:
        context = {
            'base_image': naming.image_name(config, 'root'),
            'runtime': config['runtime'],
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
    with op.docker_build_context('resources/docker/wheel-server') as build_dir:
        return op.docker_build_image(
            docker_client,
            build_dir,
            naming.image_name(config, 'wheel-server'),
            role='wheel-server',
        )


def build_runner_image(docker_client, config, name, release):
    requirement = requirements.Requirement(release)

    # Markers would not make much sense here and url are unsupported.
    assert requirement.marker is None, requirement
    assert requirement.url is None, requirement

    with op.docker_build_context('resources/docker/runner-image') as build_dir:
        context = {
            'base_image': naming.image_name(config, 'root'),
            'entrypoint_name': config['entrypoint_name'],
            'app_name': requirement.name,
            'app_extras': ','.join(sorted(requirement.extras)),
            'app_version': helpers.get_version_from_requirement(requirement),
            'volumes': config['volumes'],
            'ports': config['ports'],
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
    server_ip = container.attrs['NetworkSettings']['IPAddress']
    logger.debug('http server running with ip: %s', server_ip)
    try:
        yield server_ip
    finally:
        helpers.retry(docker.errors.APIError)(container.remove)(force=True)

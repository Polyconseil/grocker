# Copyright (c) Polyconseil SAS. All rights reserved.

import itertools
import logging

import docker.errors
import packaging.version

from . import __version__

logger = logging.getLogger(__name__)


def created_by_older_version(obj):
    grocker_version = packaging.version.parse(__version__)
    labels = obj.attrs.get('Config', obj.attrs)['Labels']
    obj_version = labels.get('grocker.version', '')
    return packaging.version.parse(obj_version) < grocker_version


def docker_purge_container(docker_client, current_version=False):
    """
    Purge Grocker internal containers.

    Args:
        docker_client (docker.DockerClient): a docker client
        current_version (bool): whether the images for current version will be deleted

    """
    removable_containers = [
        container
        for container in docker_client.containers.list(
            all=True,
            filters={'label': 'grocker.version', 'status': 'exited'},
        )
        if (
            (current_version or created_by_older_version(container))
            and container.attrs['Config']['Labels'].get('grocker.image.role') != 'runner'
        )
    ]

    for container in removable_containers:
        logger.info('Removing container %s...', container.name)
        try:
            container.remove()
        except docker.errors.APIError as e:
            logger.error(e)


def docker_purge_volumes(docker_client, current_version=False):
    """
    Purge Grocker volumes.

    Args:
        docker_client (docker.DockerClient): a docker client
        current_version (bool): whether the volumes for current version will be deleted

    """
    removable_volumes = [
        volume
        for volume in itertools.chain(
            docker_client.volumes.list(filters={'label': 'grocker.version'}),
            docker_client.volumes.list(filters={'label': 'grocker'}),  # old grocker versions
        )
        if current_version or created_by_older_version(volume)
    ]

    for volume in removable_volumes:
        logger.info('Removing volume %s...', volume.name)
        try:
            volume.remove()
        except docker.errors.APIError as e:
            logger.error(e)


def docker_purge_images(docker_client, current_version=False, runner=False):
    """
    Purge Grocker images.

    Args:
        docker_client (docker.DockerClient): a docker client
        current_version (bool): whether the images for current version will be deleted
        runner (bool): whether the runner images will be deleted

    """
    removable_images = [
        image
        for image in docker_client.images.list(filters={'label': 'grocker.version'})
        if (
            (current_version or created_by_older_version(image))
            and (runner or image.attrs.get('Labels', {}).get('grocker.image.role') == 'runner')
        )
    ]
    for image in removable_images:
        for tag in image.tags:
            logger.info('Removing image %s...', tag)
            try:
                docker_client.images.remove(tag)
            except docker.errors.APIError as e:
                logger.error(e)

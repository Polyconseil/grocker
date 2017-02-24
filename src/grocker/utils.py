# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import hashlib
import itertools
import os.path

import docker
import pkg_resources

from . import __version__
from . import helpers

GROUP_SEPARATOR = b'\x1D'
RECORD_SEPARATOR = b'\x1E'
UNIT_SEPARATOR = b'\x1F'


def config_identifier(config):
    """
    Hash config to get an unique identifier

    Args:
        config (dict): Grocker config

    Returns:
        str: Config identifier (SHA 256)
    """
    def unit_list(l):
        return UNIT_SEPARATOR.join(sorted(x.encode('utf-8') for x in l))

    dependencies = unit_list(get_dependencies(config, with_build_dependencies=True))
    repositories = RECORD_SEPARATOR.join(
        unit_list([name] + [cfg[x] for x in sorted(cfg)])
        for name, cfg in config['repositories'].items()
    )
    data = GROUP_SEPARATOR.join([
        dependencies,
        repositories,
    ])
    digest = hashlib.sha256(data)
    return digest.hexdigest()


def default_image_name(config, release):
    req = pkg_resources.Requirement.parse(release)
    assert str(req.specifier).startswith('=='), "Only fixed version can use default image name."
    docker_image_prefix = config['docker_image_prefix']
    if config['image_base_name']:
        img_name = config['image_base_name']
    elif req.extras:
        img_name = "{project}-{extra_requirements}".format(
            project=req.project_name,
            extra_requirements='-'.join(req.extras),
        )
    else:
        img_name = req.project_name
    img_name += ":{project_version}-{grocker_version}".format(
        project_version=str(req.specifier)[2:],
        grocker_version=__version__,
    )
    return '/'.join((docker_image_prefix, img_name)) if docker_image_prefix else img_name


def docker_get_client(min_version=None):
    client = docker.from_env()
    if min_version and client.version()['ApiVersion'].split('.') <= min_version.split('.'):
        raise RuntimeError(
            'Docker API version should be at least {expected} ({current})'.format(
                current=client.version()['ApiVersion'],
                expected=min_version,
            )
        )
    return client


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


def parse_config(config_paths, **kwargs):
    """
    Generate config regarding precedence order

    Precedence order is defined as :

    1. Command line arguments
    2. project ``.grocker.yml`` file (or the one specified on the command line)
    3. the grocker ``resources/grocker.yaml`` file
    """
    config = helpers.load_yaml_resource('resources/grocker.yaml')

    if not config_paths and os.path.exists('.grocker.yml'):
        config_paths = ['.grocker.yml']

    for config_path in config_paths:
        project_config = helpers.load_yaml(config_path)
        config.update(project_config or {})

    config.update({k: v for k, v in kwargs.items() if v})

    return config

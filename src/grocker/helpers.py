# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import functools
import hashlib
import io
import itertools
import json
import os.path
import shutil
import tempfile
import time

import jinja2
import pip.baseparser
import pkg_resources
import yaml

from . import __version__

GROUP_SEPARATOR = b'\x1D'
RECORD_SEPARATOR = b'\x1E'
UNIT_SEPARATOR = b'\x1F'


def copy_resource(resource, destination, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    if pkg_resources.isdir(resource_path):
        shutil.copytree(resource_path, destination)
    else:
        shutil.copy2(resource_path, destination)


def load_yaml(file_path):
    with io.open(file_path, encoding='utf-8') as fp:
        return yaml.load(fp.read())


def load_yaml_resource(resource, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    return load_yaml(resource_path)


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


def render_template(template_path, output_path, context):
    env = jinja2.Environment()
    env.filters['jsonify'] = json.dumps

    with io.open(template_path, encoding='utf-8') as template_file:
        template = env.from_string(template_file.read())

    output = template.render(**context)

    with io.open(output_path, mode='w', encoding='utf-8') as output_file:
        output_file.write(output)


def default_image_name(docker_image_prefix, release):
    req = pkg_resources.Requirement.parse(release)
    assert str(req.specifier).startswith('=='), "Only fixed version can use default image name."
    img_name = "{project}{extra_requirements}:{project_version}-{grocker_version}".format(
        project=req.project_name,
        extra_requirements='-' + '-'.join(req.extras) if req.extras else '',
        project_version=str(req.specifier)[2:],
        grocker_version=__version__,
    )
    return '/'.join((docker_image_prefix, img_name)) if docker_image_prefix else img_name


@contextlib.contextmanager
def pip_conf(pip_conf_path=None):
    """
    Use or fake (when it does not exist) a pip config file

    Args:
        pip_conf_path: str, pip configuration file to use if it exists

    Yield:
        str, the path to the pip configuration file (or the faked one)
    """
    if pip_conf_path is None or not os.path.exists(pip_conf_path):
        with tempfile.NamedTemporaryFile('w', dir=os.path.expanduser('~/.cache')) as f:
            config = pip.baseparser.ConfigOptionParser(name='global').config
            config.write(f)
            f.flush()
            yield f.name
    else:
        yield pip_conf_path


def retry(exception, tries=3, delay=1):
    def decorator(function):
        @functools.wraps(function)
        def inner(*args, **kwargs):
            for i in range(tries):
                try:
                    return function(*args, **kwargs)
                except exception:
                    if i + 1 == tries:
                        raise
                    time.sleep(delay)
        return inner
    return decorator

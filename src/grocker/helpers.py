# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import functools
import io
import json
import os.path
import shutil
import tempfile
import time

import jinja2
import pip.baseparser
import pkg_resources
import yaml


def copy_resource(resource, destination, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    if pkg_resources.isdir(resource_path):
        shutil.copytree(resource_path, destination)
    else:
        shutil.copy2(resource_path, destination)


def load_yaml(file_path):
    with io.open(file_path, encoding='utf-8') as fp:
        return yaml.load(fp.read())


def dump_yaml(file_path, data):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with io.open(file_path, 'w') as fp:
        return yaml.dump(data, stream=fp, indent=True)


def load_yaml_resource(resource, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    return load_yaml(resource_path)


def render_template(template_path, output_path, context):
    env = jinja2.Environment()
    env.filters['jsonify'] = json.dumps

    with io.open(template_path, encoding='utf-8') as template_file:
        template = env.from_string(template_file.read())

    output = template.render(**context)

    with io.open(output_path, mode='w', encoding='utf-8') as output_file:
        output_file.write(output)


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


def get_version_from_requirement(requirement):
    if len(requirement.specifier) != 1:
        raise ValueError("Only exact specifier are accepted: %s" % requirement)
    spec = list(requirement.specifier)[0]
    if spec.operator not in ('==', '==='):
        raise ValueError("Only exact specifier are accepted: %s" % requirement)
    return spec.version

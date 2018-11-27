# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import
from __future__ import unicode_literals

import contextlib
import functools
import io
import json
import os.path
import shutil
import subprocess  # noqa: S404
import tempfile
import time

import importlib_resources as resources
import jinja2
import yaml

from .six import configparser
from .six import makedirs


def copy_resources(package, destination):
    makedirs(destination, exist_ok=True)

    for entry in resources.contents(package):
        if not resources.is_resource(package, entry):
            continue

        with resources.path(package, entry) as resource_path:
            shutil.copy2(str(resource_path), destination)


def load_yaml(file_path):
    with io.open(file_path, encoding='utf-8') as fp:
        return yaml.safe_load(fp.read())


def dump_yaml(file_path, data):
    directory = os.path.dirname(file_path)
    makedirs(directory, exist_ok=True)

    with io.open(file_path, 'w') as fp:
        return yaml.safe_dump(data, stream=fp, indent=True)


def load_yaml_resource(package, name):
    with resources.path(package, name) as resource_path:
        return load_yaml(str(resource_path))


def render_template(template_path, output_path, context):
    env = jinja2.Environment()  # noqa: S701
    env.filters['jsonify'] = json.dumps

    with io.open(template_path, encoding='utf-8') as template_file:
        template = env.from_string(template_file.read())

    output = template.render(**context)

    with io.open(output_path, mode='w', encoding='utf-8') as output_file:
        output_file.write(output)


@contextlib.contextmanager
def pip_conf(pip_conf_path=None):
    """
    Use or fake (when it does not exist) a pip config file.

    Args:
        pip_conf_path: str, pip configuration file to use if it exists

    Yield:
        str, the path to the pip configuration file (or the faked one)
    """
    if pip_conf_path is None or not os.path.exists(pip_conf_path):
        with tempfile.NamedTemporaryFile('w', dir=os.path.expanduser('~/.cache')) as f:
            config = configparser.RawConfigParser()
            config.add_section('global')
            for key in ['index-url', 'timeout', 'extra-index']:
                try:
                    output = subprocess.check_output(  # noqa: S603,S607
                        ['pip', 'config', 'get', 'global.{}'.format(key)],
                    )
                    value = output.decode().strip()
                    config.set('global', key, value)
                except subprocess.CalledProcessError:
                    pass
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

# Copyright (c) Polyconseil SAS. All rights reserved.

import configparser
import contextlib
import functools
import json
import os
import os.path
import shutil
import subprocess  # noqa: S404
import tempfile
import time
from importlib import resources

import jinja2
import yaml


def deep_update(initial_mapping, updating_mapping):
    updated_mapping = initial_mapping.copy()
    for k, v in updating_mapping.items():
        if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
            updated_mapping[k] = deep_update(updated_mapping[k], v)
        else:
            updated_mapping[k] = v
    return updated_mapping


def copy_resources(package, destination):
    os.makedirs(destination, exist_ok=True)

    for entry in resources.contents(package):
        if not resources.is_resource(package, entry):
            continue

        with resources.path(package, entry) as resource_path:
            shutil.copy2(str(resource_path), destination)


def load_yaml(file_path):
    with open(file_path, encoding='utf-8') as fp:
        return yaml.safe_load(fp.read())


def dump_yaml(file_path, data):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)

    with open(file_path, 'w') as fp:
        return yaml.safe_dump(data, stream=fp, indent=True)


def load_yaml_resource(package, name):
    with resources.path(package, name) as resource_path:
        return load_yaml(str(resource_path))


def render_template(template_path, output_path, context):
    env = jinja2.Environment()  # noqa: S701
    env.filters['jsonify'] = json.dumps

    with open(template_path, encoding='utf-8') as template_file:
        template = env.from_string(template_file.read())

    output = template.render(**context)

    with open(output_path, mode='w', encoding='utf-8') as output_file:
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
        with tempfile.NamedTemporaryFile('w') as f:
            config = configparser.RawConfigParser()
            config.add_section('global')
            for key in ['index-url', 'timeout', 'extra-index']:
                try:
                    output = subprocess.check_output(  # noqa: S603,S607
                        ['pip', 'config', 'get', f'global.{key}'],
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

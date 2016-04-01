# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import hashlib
import io
import os.path
import shutil
import tempfile

import jinja2
import pip.baseparser
import pkg_resources
import yaml

from . import __version__

UNIT_SEPARATOR = b'\x1F'


def copy_resource(resource, destination, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    if pkg_resources.isdir(resource_path):
        shutil.copytree(resource_path, destination)
    else:
        shutil.copy2(resource_path, destination)


def load_yaml(file_path):
    if not os.path.exists(file_path):
        return None
    with io.open(file_path, encoding='utf-8') as fp:
        return yaml.load(fp.read())


def load_yaml_resource(resource, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    return load_yaml(resource_path)


def hash_list(l):
    digest = hashlib.sha256(UNIT_SEPARATOR.join(x.encode('utf-8') for x in l))
    return digest.hexdigest()


def render_template(template_path, output_path, context):
    with io.open(template_path, encoding='utf-8') as template_file:
        template = jinja2.Template(template_file.read())

    output = template.render(**context)

    with io.open(output_path, mode='w', encoding='utf-8') as output_file:
        output_file.write(output)


def default_image_name(docker_registry, release):
    req = pkg_resources.Requirement.parse(release)
    assert str(req.specifier).startswith('=='), "Only fixed version can use default image name."
    return "{registry}/{project}{extra_requirements}:{project_version}-{grocker_version}".format(
        registry=docker_registry,
        project=req.project_name,
        extra_requirements='-' + '-'.join(req.extras) if req.extras else '',
        project_version=str(req.specifier)[2:],
        grocker_version=__version__,
    )


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

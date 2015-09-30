# -*- coding: utf-8 -*-
# Copyright (c) 2011-2015 Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import io
import os.path
import shutil
import tempfile

import jinja2
import pip.baseparser
import pkg_resources

from . import __version__


def copy_resource(resource, destination, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    if pkg_resources.isdir(resource_path):
        shutil.copytree(resource_path, destination)
    else:
        shutil.copy2(resource_path, destination)


def render_template(template_path, output_path, context):
    with io.open(template_path, encoding='utf-8') as template_file:
        template = jinja2.Template(template_file.read())

    output = template.render(**context)

    with io.open(output_path, mode='w', encoding='utf-8') as output_file:
        output_file.write(output)


def default_image_name(docker_registry, release):
    req = pkg_resources.Requirement.parse(release)
    assert str(req.specifier).startswith('=='), "Only fixed version can use default image name."
    return "{}/{}{}:{}-{}".format(
        docker_registry,
        req.project_name,
        '-' + '-'.join(req.extras) if req.extras else '',
        str(req.specifier)[2:],
        __version__,
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
        with tempfile.NamedTemporaryFile('w') as f:
            config = pip.baseparser.ConfigOptionParser(name='global').config
            config.write(f)
            f.flush()
            yield f.name
    else:
        yield pip_conf_path

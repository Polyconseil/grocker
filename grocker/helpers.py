# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import contextlib
import io
import os.path
import shutil
import tempfile
import threading

import jinja2
import pip.baseparser
import pkg_resources
import yaml

from . import six
from . import __version__


def copy_resource(resource, destination, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    if pkg_resources.isdir(resource_path):
        shutil.copytree(resource_path, destination)
    else:
        shutil.copy2(resource_path, destination)


def load_yaml_resource(resource, package='grocker'):
    resource_path = pkg_resources.resource_filename(package, resource)
    with io.open(resource_path, encoding='utf-8') as fp:
        return yaml.load(fp.read())


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


class SimpleHTTPServer(six.ThreadingMixIn, six.HTTPServer):
    def __init__(self, package_dir, server_address):  # pylint: disable=super-init-not-called
        six.super6(
            SimpleHTTPServer, self, '__init__',
            server_address, six.SimpleHTTPRequestHandler, bind_and_activate=False
        )
        self.package_dir = package_dir

    def serve_forever(self, poll_interval=0.5):
        os.chdir(self.package_dir)
        six.super6(SimpleHTTPServer, self, 'serve_forever', poll_interval=poll_interval)

    def __enter__(self):
        self.server_bind()
        self.server_activate()
        threading.Thread(target=self.serve_forever).start()

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


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

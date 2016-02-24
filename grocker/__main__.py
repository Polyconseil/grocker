#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import collections
import enum
import logging
import os
import os.path
import subprocess

from . import __version__
from . import builders
from . import helpers
from . import loggers
from . import six


Image = collections.namedtuple('Image', ['name', 'sha256'])


class GrockerActions(enum.Enum):
    build_dep = 'dep'  # -> dep
    build_img = 'img'  # -> img
    push_img = 'push'  # -> push
    all = 'build'  # -> dep + img + push


def arg_parser():
    def file_path_type(x):
        return os.path.abspath(os.path.expanduser(x))

    def file_path_or_none_type(x):
        return file_path_type(x) if x is not None else None

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r', '--runtime', default='python', choices=('python', 'python3'),
        help="runtime used to build and run this image.",
    )
    parser.add_argument(
        '-e', '--entry-point', metavar='<package>', dest='entrypoint', default='grocker-pyapp',
        help="entrypoint used to run this image.",
    )
    parser.add_argument(
        '--package-dir', metavar='<dir>', type=file_path_type, default='~/.cache/grocker/packages',
        help="store build dependencies in this directory.",
    )
    parser.add_argument(
        '--pip-conf', metavar='<file>', type=file_path_or_none_type, default=None,
        help="pip configuration file used to download dependencies (by default use pip config getter).",
    )
    parser.add_argument(
        '--pip-constraint', metavar='<file>', type=file_path_or_none_type, default=None,
        help="pip constraint file used to download dependencies.",
    )
    parser.add_argument(
        '--docker-registry', metavar='<url>',
        default='docker.polydev.blue',  # TODO(fbochu): Use config to define default registry
        help='docker registry or account on Docker official registry to use.'
    )
    parser.add_argument('-n', '--image-name', metavar='<name>', help="name used to tag the build image.")
    parser.add_argument(
        'action', choices=GrockerActions, type=GrockerActions, nargs='+',
        metavar='<action>', help='should be one of {}.'.format(', '.join(x.value for x in GrockerActions))
    )
    parser.add_argument('release', metavar='<release>', help="application to build (you can use version specifier).")

    parser.add_argument('--no-check-version', action='store_true', help='do not check if Grocker is up to date.')
    parser.add_argument('--purge', action=PurgeAction, help="purge docker images")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')

    return parser


class PurgeAction(argparse.Action):
    """Argparse action to purge grocker related docker images"""

    def __init__(self, option_strings, *args, **kwargs):
        super(PurgeAction, self).__init__(
            option_strings=option_strings,
            dest=argparse.SUPPRESS,
            choices=('all', 'build', 'dangling', 'run'),
        )

    def __call__(self, parser, namespace, values, *args, **kwargs):
        filters = [values] if values != 'all' else (x for x in self.choices if x != 'all')
        builders.docker_purge_images(builders.docker_get_client(), filters)
        parser.exit()


def is_grocker_outdated(skip=False):
    logger = logging.getLogger(__name__)
    if not skip and 'grocker' in six.smart_text(subprocess.check_output(['pip', 'list',  '--outdated'])):
        logger.critical('Grocker needs to be updated')
        return True
    return False


def main(args=None):
    parser = arg_parser()
    args = parser.parse_args(args)
    if GrockerActions.all in args.action:
        args.action = set(GrockerActions) - {GrockerActions.all}

    loggers.setup(verbose=args.verbose)
    logger = logging.getLogger('grocker' if __name__ == '__main__' else __name__)
    docker_client = builders.docker_get_client()
    image_name = args.image_name or helpers.default_image_name(args.docker_registry, args.release)

    logger.info('Checking prerequisites...')
    if builders.is_docker_outdated(docker_client):
        raise RuntimeError('Docker is outdated')

    if is_grocker_outdated(skip=args.no_check_version):
        raise RuntimeError('Grocker is outdated')

    if GrockerActions.build_dep in args.action:
        logger.info('Compiling dependencies...')
        compiler_tag = builders.get_compiler_image(docker_client, args.docker_registry)
        with helpers.pip_conf(pip_conf_path=args.pip_conf) as pip_conf:
            builders.compile_wheels(
                docker_client=docker_client,
                compiler_tag=compiler_tag,
                python=args.runtime,
                release=args.release,
                entrypoint=args.entrypoint,
                package_dir=args.package_dir,
                pip_conf=pip_conf,
                pip_constraint=args.pip_constraint,
            )

    if GrockerActions.build_img in args.action:
        logger.info('Building image...')
        root_image_tag = builders.get_root_image(docker_client, args.docker_registry)
        builders.build_runner_image(
            docker_client=docker_client,
            root_image_tag=root_image_tag,
            entrypoint=args.entrypoint,
            runtime=args.runtime,
            release=args.release,
            package_dir=args.package_dir,
            pip_constraint=args.pip_constraint,
            tag=image_name,
        )

    if GrockerActions.push_img in args.action:
        logger.info('Pushing image...')
        sha256 = builders.docker_push_image(docker_client, image_name)
        return Image(image_name, sha256)


if __name__ == '__main__':
    main()

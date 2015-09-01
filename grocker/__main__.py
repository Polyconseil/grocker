#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2011-2015 Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import enum
import logging
import os
import os.path

from . import __version__
from . import builders
from . import helpers
from . import loggers


ACTIONS = enum.Enum('GrockerActions', names={
    'build_dep': 'build-dependencies',
    'build_img': 'build-image',
    'only_build_img': 'only-build-image',
})


def arg_parser():
    def file_path_type(x):
        return os.path.abspath(os.path.expanduser(x))

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--runtime', default='python', choices=('python', 'python3'),
        help="Runtime used to build and run this image.",
    )
    parser.add_argument(
        '--entry-point', dest='entrypoint', default='grocker-pyapp',
        help="Entrypoint used to run this image.",
    )
    parser.add_argument(
        '--package-dir', type=file_path_type, default='./build/packages',
        help="Store build dependencies in this directory.",
    )
    parser.add_argument(
        '--pip-conf', type=file_path_type, default='~/.pip/pip.conf',
        help="Pip configuration file used to download dependencies (only index-url is used).",
    )
    parser.add_argument(
        '--docker-registry',
        default='docker.polydev.blue',  # TODO(fbochu): Use config to define default registry
        help='Docker registry or account on Docker official registry to use.'
    )
    parser.add_argument('--image-name', help="name used to tag the build image.")
    parser.add_argument(
        'action', choices=ACTIONS, type=ACTIONS,
        metavar='<action>', help='Should be on of {}.'.format(', '.join(x.value for x in ACTIONS))
    )
    parser.add_argument('release', metavar='<release>', help="Application to build (you can use version specifier).")

    parser.add_argument('--purge', action=PurgeAction, help="Purge docker images")
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--verbose', action='store_true', help='Verbose mode')

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


def main():
    parser = arg_parser()
    args = parser.parse_args()

    loggers.setup(verbose=args.verbose)
    logger = logging.getLogger('grocker' if __name__ == '__main__' else __name__)
    docker_client = builders.docker_get_client()

    if args.action in (ACTIONS.build_dep, ACTIONS.build_img):
        logger.info('Compiling dependencies...')
        compiler_tag = builders.get_compiler_image(docker_client, args.docker_registry)
        builders.compile_wheels(
            docker_client=docker_client,
            compiler_tag=compiler_tag,
            python=args.runtime,
            release=args.release,
            entrypoint=args.entrypoint,
            package_dir=args.package_dir,
            pip_conf=args.pip_conf,
        )

    if args.action in (ACTIONS.build_img, ACTIONS.only_build_img):
        logger.info('Building image...')
        root_image_tag = builders.get_root_image(docker_client, args.docker_registry)
        builders.build_runner_image(
            docker_client=docker_client,
            root_image_tag=root_image_tag,
            entrypoint=args.entrypoint,
            runtime=args.runtime,
            release=args.release,
            package_dir=args.package_dir,
            tag=args.image_name or helpers.default_image_name(args.docker_registry, args.release),
        )

if __name__ == '__main__':
    main()

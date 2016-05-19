#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
import argparse
import collections
import enum
# pylint: disable=wrong-import-order
import logging
import os
import os.path
import subprocess
import sys
# pylint: enable=wrong-import-order

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
    """
    Create an CLI args parser

    Some default value (marked as #precedence) are set to None due to precedence
    order (see parse_config() doc string for more information).
    """
    def file_path_type(x):
        return os.path.abspath(os.path.expanduser(x))

    def file_path_or_none_type(x):
        return file_path_type(x) if x is not None else None

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', type=file_path_or_none_type, default='./.grocker.yml',
        help='Grocker config file',
    )
    parser.add_argument(  # precedence
        '-r', '--runtime', default=None,
        help="runtime used to build and run this image.",
    )
    parser.add_argument(  # precedence
        '-e', '--entrypoint-name', default=None,
        help="Docker entrypoint to use to run this image.",
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
        '--docker-image-prefix', metavar='<url>',
        help='docker registry or account on Docker official registry to use.'
    )
    parser.add_argument('-n', '--image-name', metavar='<name>', help="name used to tag the build image.")
    parser.add_argument(
        'actions', choices=GrockerActions, type=GrockerActions, nargs='+',
        metavar='<actions>', help='should be one of {}.'.format(', '.join(x.value for x in GrockerActions))
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
        filters = [values] if values != 'all' else [x for x in self.choices if x != 'all']
        builders.docker_purge_images(builders.docker_get_client(), filters)
        builders.docker_purge_volumes(builders.docker_get_client(), filters)
        parser.exit()


def is_grocker_outdated(skip=False):
    logger = logging.getLogger(__name__)
    if not skip:
        words = [line.split(' ')[0] for line in six.smart_text(
            subprocess.check_output(['pip', 'list', '--outdated'])
        ).splitlines()]
        if 'grocker' in words:
            logger.critical('Grocker needs to be updated')
            return True
    return False


def parse_config(config_path, **kwargs):
    """
    Generate config regarding precedence order

    Precedence order is defined as :

    1. Command line arguments
    2. project ``.grocker.yml`` file (or the one specified on the command line)
    3. the grocker ``resources/grocker.yaml`` file
    """
    config = helpers.load_yaml_resource('resources/grocker.yaml')
    project_config = helpers.load_yaml(config_path) or {}

    config.update(project_config)
    config.update({k: v for k, v in kwargs.items() if v})

    return config


def clean_actions(actions):
    if GrockerActions.all in actions:
        actions_without_all = set(GrockerActions) - {GrockerActions.all}
        if actions != [GrockerActions.all]:
            sys.exit(
                "The {all} action already specifies {actions_without_all}.\n"
                "Please use either {all} or any combination of ({actions_without_all}).".format(
                    all=GrockerActions.all.value,
                    actions_without_all=', '.join(sorted(action.value for action in actions_without_all)),
                )
            )
        actions = actions_without_all
    return actions


def main(cli_args=None):
    parser = arg_parser()
    args = parser.parse_args(cli_args)
    config = parse_config(
        args.config,
        runtime=args.runtime,
        entrypoint_name=args.entrypoint_name,
        pip_constraint=args.pip_constraint,
        docker_image_prefix=args.docker_image_prefix,
    )

    loggers.setup(verbose=args.verbose)
    logger = logging.getLogger('grocker' if __name__ == '__main__' else __name__)

    args.actions = clean_actions(args.actions)

    if config['runtime'] not in config['system']['runtime']:
        raise RuntimeError('Unknown runtime: %s', config['runtime'])

    docker_client = builders.docker_get_client()
    image_name = args.image_name or helpers.default_image_name(config['docker_image_prefix'], args.release)

    logger.info('Checking prerequisites...')
    if builders.is_docker_outdated(docker_client):
        raise RuntimeError('Docker is outdated')

    if is_grocker_outdated(skip=args.no_check_version):
        raise RuntimeError('Grocker is outdated')

    wheels_volume_name = 'grocker-wheels-cache-{version}-{hash}'.format(
        version=__version__,
        hash=helpers.hash_list(builders.get_dependencies(config)),
    )

    if GrockerActions.build_dep in args.actions:
        logger.info('Compiling dependencies...')
        compiler_tag = builders.get_compiler_image(docker_client, config)
        with helpers.pip_conf(pip_conf_path=args.pip_conf) as pip_conf:
            builders.compile_wheels(
                docker_client=docker_client,
                compiler_tag=compiler_tag,
                config=config,
                release=args.release,
                wheels_volume_name=wheels_volume_name,
                pip_conf=pip_conf,
            )

    if GrockerActions.build_img in args.actions:
        logger.info('Building image...')
        root_image_tag = builders.get_root_image(docker_client, config)
        builders.build_runner_image(
            docker_client=docker_client,
            root_image_tag=root_image_tag,
            config=config,
            release=args.release,
            wheels_volume_name=wheels_volume_name,
            tag=image_name,
        )

    if GrockerActions.push_img in args.actions:
        if '/' not in image_name:
            logger.warning('Not pushing any image since the registry is unclear in %s', image_name)
            sha256 = None
        else:
            logger.info('Pushing image...')
            sha256 = builders.docker_push_image(docker_client, image_name)
        return Image(image_name, sha256)


if __name__ == '__main__':
    main()

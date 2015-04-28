#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Docker Builder for Blue Applications

    Aims at compiling / preparing releases in a docker to be available when creating a new target docker.

    prerequisites: the user running the program should be able to run the docker command.
    - On debian, there is a docker group, so adding your user and logout / re-login would work.
      $ sudo usermod -a -G docker ${USER}

"""
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import logging
import logging.config
import os
import re
import subprocess
import sys
import textwrap


__version__ = '0.1'
REQUIRED_IMAGE_NAMES = ('base', 'compiler')
BLUE_HOME = '/home/blue'

RUNNER_BUILD_DIR = './bundles/runner/output'  # the runner's Dockerfile needs access to this folder
RUNNER_ENV_FILE = 'config.env'
RUNNER_ENV_FILE_TPL = """
    PROJECT_NAME={project}
    PROJECT_VERSION={version}
    PACKAGE_NAME={package}
    PYTHON_VERSION={python_version}
"""


def main():
    args = builder_arg_parser(sys.argv[1:])

    setup_logging(not args.no_colors)

    # TODO: should be one of the targets of this script. make build_images with one of the "machines" as parameter.
    for name in REQUIRED_IMAGE_NAMES:
        build_docker_image(name)

    # TODO: same, this is again a different target. should be separate.
    build_dir = args.build_dir or RUNNER_BUILD_DIR
    if not os.path.exists(build_dir):
        os.makedirs(build_dir, mode=0o0750)
    compile_packages(args.package, python_version=args.python_version, build_dir=build_dir)

    # TODO: last but not least, go with the Makefile for this.
    if args.build_dir is None:
        build_runner(args.package, python_version=args.python_version, build_dir=build_dir)


def builder_arg_parser(argv):
    parser = argparse.ArgumentParser(prog='BlueSolutions Application Image Builder')
    parser.add_argument('--version', action='version', version='%(prog)s {0}'.format(__version__))

    parser.add_argument(
        '--python',
        metavar='PYTHON_VERSION',
        dest='python_version',
        help="Python version to build and use for the instance",
        required=True,
    )

    parser.add_argument('--no-colors', help="Do not use colored output", action='store_true')
    parser.add_argument('--build-dir', help="Build dependencies in this directory (runner image will not be built).")
    parser.add_argument('package', type=_versioned_package, help="The project to build (format: <name>==<version>)")

    return parser.parse_args(argv)


def _versioned_package(value):
    if not re.match(r'\w(\w|-)+==\d+.\d+.\d+', value):
        raise argparse.ArgumentTypeError("Do not match <name>==<x>.<y>.<z> pattern.")
    return value


def build_docker_image(name):
    run(
        'docker', 'build',
        '--force-rm=true', '--rm=true',
        '-t', 'docker.polyconseil.fr/bundle-{name}:{version}'.format(name=name, version=__version__),
        'bundles/{name}/.'.format(name=name),
    )


def compile_packages(package, build_dir, python_version=None):
    run(
        'docker', 'run',
        '--rm',
        '--volume', '{home}/.pip/:{blue_home}/.pip.host'.format(home=os.path.expanduser("~"), blue_home=BLUE_HOME),
        '--volume', '{build_dir}:{blue_home}/output'.format(build_dir=os.path.abspath(build_dir), blue_home=BLUE_HOME),

        'docker.polyconseil.fr/bundle-compiler:{builder_version}'.format(builder_version=__version__),

        '--output', '{blue_home}/output'.format(blue_home=BLUE_HOME),
        '--python', python_version,
        package
    )


def build_runner(package, build_dir, python_version=None):
    # create env file
    env_file_path = os.path.join(build_dir, RUNNER_ENV_FILE)
    with open(env_file_path, 'w') as env_file:
        env_file.write(
            textwrap
            .dedent(RUNNER_ENV_FILE_TPL)
            .format(
                package=package,
                project=package.split('==')[0],
                version=package.split('==')[1],
                python_version=python_version
            )
        )

    # create the future docker image
    run(
        'docker', 'build',
        '--force-rm=true', '--rm=true',
        '-t', 'docker.polyconseil.fr/{0}'.format(package.replace('==', ':')),
        'bundles/runner/.'
    )


def setup_logging(enable_colors):
    colors = {'begin': '\033[1;33m', 'end': '\033[0m'}
    if not enable_colors:
        colors = {'begin': '', 'end': ''}

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {
                'format': '{begin}%(message)s{end}'.format(**colors)
            },
        },
        'handlers': {
            'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        },
        'loggers': {
            __name__: {'handlers': ['console'], 'level': 'INFO'},
        },
    })


def run(*args):
    logging.getLogger(__name__).info("-> running %s", ' '.join(args))
    try:
        subprocess.check_call(args)
    except subprocess.CalledProcessError:
        sys.exit(1)

if __name__ == '__main__':
    main()
#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals
import argparse
import logging
import logging.config
import os.path
import subprocess
import sys
import tempfile

try:  # Python 3+
    import configparser
except ImportError:  # Python 2.7
    import ConfigParser as configparser


def arg_parser():
    file_validator = os.path.expanduser

    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default='python')
    parser.add_argument('--pip-conf', type=file_validator)
    parser.add_argument('--package-dir', type=file_validator, default='~/packages')
    parser.add_argument('--no-color', action='store_true')
    parser.add_argument('release', nargs='+')

    return parser


def setup_logging(enable_colors):
    colors = {'begin': '\x1b[1;36m', 'end': '\x1b[0m'} if enable_colors else {'begin': '', 'end': ''}

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {'format': '{begin}%(message)s{end}'.format(**colors)},
        },
        'handlers': {
            'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
        },
        'loggers': {
            __name__: {'handlers': ['console'], 'level': 'INFO'},
        },
    })


def info(*msg):
    logging.getLogger(__name__).info(*msg)


def setup_pip(venv, pip_conf, package_dir):
    """Parse host pip.conf to generate venv pip.conf."""
    info('Setup pip...')

    # Standard config
    guest_config = configparser.ConfigParser()
    guest_config.add_section('global')
    guest_config.set('global', 'wheel-dir', package_dir)
    guest_config.set('global', 'find-links', package_dir)

    # Specific config
    if pip_conf:
        info('-> Pip use specific configuration form %s.', pip_conf)
        specified_config = configparser.ConfigParser()
        if specified_config.read(pip_conf):
            guest_config.set('global', 'index-url', specified_config.get('global', 'index-url'))
            guest_config.set('global', 'extra-index-url', specified_config.get('global', 'extra-index-url'))
        else:
            info('-> Unable to read config.')

    # Write config
    venv_pip_conf = os.path.join(venv, 'pip.conf')
    with open(venv_pip_conf, 'w') as f:
        guest_config.write(f)


def setup_venv(python):
    """Setup venv and return python interpreter."""
    info('Setup venv using %s...', python)
    venv = tempfile.mkdtemp(suffix='.venv')
    subprocess.check_call(['virtualenv', '-p', python, venv])
    subprocess.check_call([os.path.join(venv, 'bin', 'pip'), 'install', '-U', 'pip', 'setuptools', 'wheel'])
    return venv


def build_wheels(venv, package, package_dir):
    info('Building wheels for %s...', package)
    pip = os.path.join(venv, 'bin', 'pip')
    try:
        subprocess.check_call([pip, 'wheel', '--wheel-dir', package_dir, package])
    except subprocess.CalledProcessError as exc:
        info(str(exc))
        if exc.output:
            print(exc.output)
        exit(1)


def main():
    parser = arg_parser()
    args = parser.parse_args(sys.argv[1:])
    setup_logging(not args.no_color)

    venv = setup_venv(args.python)
    setup_pip(venv, args.pip_conf, args.package_dir)

    for release in args.release:
        build_wheels(venv, release, args.package_dir)


if __name__ == '__main__':
    main()

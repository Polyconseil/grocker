# Copyright (c) Polyconseil SAS. All rights reserved.

import argparse
import base64
import configparser
import logging
import logging.config
import os
import os.path
import subprocess  # noqa: S404
import tempfile
import zlib

WHEELS_DIRECTORY = os.path.expanduser('~/packages')


def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', default='python')
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


def setup_pip(venv, package_dir):
    """Generate venv pip.conf."""
    info('Setup pip...')

    # Standard config
    guest_config = configparser.ConfigParser()
    guest_config.add_section('global')
    guest_config.set('global', 'wheel-dir', package_dir)
    guest_config.set('global', 'find-links', package_dir)

    # Write config
    venv_pip_conf = os.path.join(venv, 'pip.conf')
    with open(venv_pip_conf, 'w') as f:
        guest_config.write(f)


def setup_venv(python):
    """Return python interpreter after setup the venv."""
    info('Setup venv using %s...', python)
    venv = tempfile.mkdtemp(suffix='.venv')
    try:
        # python 3
        subprocess.check_call([python, '-m', 'venv', venv])  # noqa: S603
    except subprocess.CalledProcessError:
        subprocess.check_call([python, '-m', 'virtualenv', venv])  # noqa: S603
    subprocess.check_call(  # noqa: S603
        [os.path.join(venv, 'bin', 'pip'), 'install', '-U', 'pip', 'setuptools', 'wheel'],
    )
    return venv


def build_wheels(venv, package, package_dir, constraint=None):
    info('Building wheels for %s...', package)
    pip = os.path.join(venv, 'bin', 'pip')
    constraint_args = ['--constraint', constraint] if constraint else []
    try:
        subprocess.check_call(  # noqa: S603
            [pip, 'wheel', '--wheel-dir', package_dir]
            + constraint_args
            + [package],
        )
        return True
    except subprocess.CalledProcessError as exc:
        info(str(exc))
        if exc.output:
            print(exc.output)
        return False


def main():
    parser = arg_parser()
    args = parser.parse_args()
    setup_logging(not args.no_color)

    venv = setup_venv(args.python)
    setup_pip(venv, WHEELS_DIRECTORY)

    constraints = os.environ.get('PIP_CONSTRAINT_CONTENT', base64.b64encode(zlib.compress(b'')))
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(zlib.decompress(base64.b64decode(constraints)))
        fp.flush()

        for release in args.release:
            if not build_wheels(venv, release, WHEELS_DIRECTORY, fp.name):
                exit(1)


if __name__ == '__main__':
    main()

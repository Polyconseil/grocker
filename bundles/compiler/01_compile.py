#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, print_function, unicode_literals
import argparse
import ConfigParser as configparser
import os.path
import subprocess
import sys


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('package')
    parser.add_argument('--python')
    parser.add_argument('--output')

    args = parser.parse_args(argv[1:])

    output_dir = args.output

    host_pip_conf = os.path.expanduser('~/.pip.host/pip.conf')
    guest_pip_conf = os.path.expanduser('~/.pip/pip.conf')
    venv_dir = os.path.expanduser('~/venv')

    # Parse host pip.conf to generate guest pip.conf
    host_config = configparser.ConfigParser()
    host_config.read(host_pip_conf)
    guest_config = configparser.ConfigParser()
    guest_config.add_section('global')
    guest_config.set('global', 'index-url', host_config.get('global', 'index-url'))
    guest_config.set('global', 'extra-index-url', host_config.get('global', 'extra-index-url'))
    guest_config.set('global', 'wheel-dir', output_dir)
    guest_config.set('global', 'find-links', output_dir)

    with open(guest_pip_conf, 'w') as f:
        guest_config.write(f)

    # Prepare to Build Wheels
    subprocess.check_call(['virtualenv', '-p', 'python{0}'.format(args.python), venv_dir])
    pip = os.path.join(venv_dir, 'bin', 'pip')
    subprocess.check_call([pip, 'install', '-U', 'pip', 'setuptools', 'wheel'])

    # Build wheels
    try:
        subprocess.check_call([pip, 'wheel', '--wheel-dir', output_dir, args.package])
    except subprocess.CalledProcessError as exc:
        print(exc.output)


if __name__ == '__main__':
    main(sys.argv)
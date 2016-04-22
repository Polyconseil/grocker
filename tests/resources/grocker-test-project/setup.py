#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
from setuptools import setup, find_packages

from gtp import __version__


setup(
    name='grocker-test-project',
    description='Test project for Grocker',
    url='http://github.com/polyconseil/grocker',
    author='Polyconseil',
    author_email='TBD on first public release',
    version=__version__,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'zbarlight',  # dependency using C modules
        'qrcode',
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'grocker-runner = gtp.__main__:main',
        ],
    },
)

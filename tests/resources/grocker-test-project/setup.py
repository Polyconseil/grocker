#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals
from setuptools import setup, find_packages

setup(
    name='grocker-test-project',
    description='Test project for Grocker',
    url='http://github.com/polyconseil/grocker',
    author='Polyconseil',
    author_email='TBD on first public release',
    version='2.0.0',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'zbarlight',  # dependency using C modules
        'qrcode',
    ],
    extras_require={'pep8': ['pep8==1.7.0']},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'grocker-runner = gtp.__main__:main',
            'my-custom-runner = gtp.__main__:custom',
        ],
    },
)

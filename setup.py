#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.
from __future__ import absolute_import, division, print_function, unicode_literals
import io

from setuptools import setup, find_packages


def read(filename):
    with io.open(filename) as f:
        return f.read()


setup(
    name='grocker',
    version='4.0.dev1',
    description="Docker image builder",
    long_description=read('Readme.rst'),
    keywords='docker build packaging',
    url='http://github.com/polyconseil/grocker',
    author='Polyconseil',
    author_email='TBD on first public release',
    license='TBD on first public release',
    packages=find_packages(where='src', exclude=('tests', 'docs')),
    package_dir={'': str('src')},
    include_package_data=True,
    install_requires=[
        'docker-py',
        'Jinja2',
        'setuptools>=18.0.1',
        'pip>=7.1.2',
        'pyyaml>=3.11',
    ],
    extras_require={
        ":python_version == '2.7'": [
            'enum34',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Software Distribution',
    ],
    entry_points={
        'console_scripts': (
            'grocker = grocker.__main__:main',
        ),
    },
)

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.
from setuptools import setup, find_packages


def read(filename):
    with open(filename) as f:
        return f.read()


setup(
    name='grocker',
    version='4.2',
    description="Docker image builder",
    long_description=read('Readme.rst'),
    keywords='docker build packaging',
    url='http://github.com/polyconseil/grocker',
    author='Polyconseil',
    author_email='opensource+grocker@polyconseil.fr',
    packages=find_packages(where='src', exclude=('tests', 'docs')),
    package_dir={'': str('src')},
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        'docker-py!=1.10.*',
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
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Software Distribution',
    ],
    entry_points={
        'console_scripts': (
            'grocker = grocker.__main__:main',
        ),
    },
)

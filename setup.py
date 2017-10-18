#! /usr/bin/env python
from setuptools import setup


setup(
    setup_requires=['setuptools>=30.3'],
    package_dir={  # FIXME: wait for https://github.com/pypa/setuptools/issues/1136
        '': 'src',
    },
)

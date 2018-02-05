#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import
from __future__ import unicode_literals

import shutil
import tempfile

# pylint: disable=unused-import,import-error
try:
    import configparser
except ImportError:
    import ConfigParser as configparser  # noqa
# pylint: enable=unused-import,import-error


class TemporaryDirectory(object):
    """Create and return a temporary directory.

    This has the same behavior as mkdtemp but can be used as a context manager.
    For example:

        with TemporaryDirectory() as tmpdir:
            ...

    Upon exiting the context, the directory and everything contained
    in it are removed.
    """

    def __init__(self, suffix="", prefix="tmp", directory=None):
        self.name = tempfile.mkdtemp(suffix, prefix, directory)

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.name)

    def __enter__(self):
        return self.name

    def __exit__(self, exc, _value, _tb):
        shutil.rmtree(self.name)

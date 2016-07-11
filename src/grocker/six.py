#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import shutil
import tempfile
import types

# pylint: disable=unused-import,import-error
try:
    import configparser
except ImportError:
    import ConfigParser as configparser  # noqa
# pylint: enable=unused-import,import-error


def super6(cls, self, method, *args, **kwargs):
    """
    A kind of super() working on both old style and new style classes.
    """
    classobj = getattr(types, 'ClassType', type(None))
    if isinstance(cls, classobj):
        getattr(cls.__bases__[-1], method)(self, *args, **kwargs)
    else:
        getattr(super(cls, self), method)(*args, **kwargs)


class TemporaryDirectory(object):
    """Create and return a temporary directory.  This has the same
    behavior as mkdtemp but can be used as a context manager.  For
    example:

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

    def __exit__(self, exc, value, tb):
        shutil.rmtree(self.name)


def smart_text(text, encoding='utf-8'):
    return text.decode(encoding) if isinstance(text, bytes) else text

#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import, division, print_function, unicode_literals

import ctypes
import os
import shutil
import tempfile
import types

try:
    from socketserver import ThreadingMixIn
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import configparser
except ImportError:
    from SocketServer import ThreadingMixIn
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    import ConfigParser as configparser


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


def sync():
    if hasattr(os, 'sync'):
        os.sync()
    else:
        try:
            libc = ctypes.CDLL("libc.so.6")
            libc.sync()
        except OSError:
            pass


def smart_text(text, encoding='utf-8'):
    return text.decode(encoding) if isinstance(text, bytes) else text

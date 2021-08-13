#! /usr/bin/env python
# Copyright (c) Polyconseil SAS. All rights reserved.

import os
import os.path
import shutil
import tempfile

# pylint: disable=unused-import,import-error
try:
    import configparser
except ImportError:
    import ConfigParser as configparser  # noqa
# pylint: enable=unused-import,import-error


class TemporaryDirectory:
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
        return f"<{self.__class__.__name__} {self.name!r}>"

    def __enter__(self):
        return self.name

    def __exit__(self, exc, _value, _tb):
        shutil.rmtree(self.name)


def makedirs(name, mode=0o777, exist_ok=False):
    if exist_ok and os.path.exists(name):
        return
    os.makedirs(name, mode=mode)

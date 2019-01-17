# -*- coding: utf-8 -*-
# Copyright (c) Polyconseil SAS. All rights reserved.

from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import warnings

import pkg_resources

__version__ = pkg_resources.get_distribution('grocker').version
__copyright__ = '2015, Polyconseil'


class GrockerDeprecationWarning(Warning):
    pass


if tuple(sys.version_info[:2]) in ((2, 7), (3, 4), (3, 5)):
    warnings.warn(
        "Support for 2.7, 3.4 and 3.5 will be dropped in next major version",
        category=GrockerDeprecationWarning,
    )

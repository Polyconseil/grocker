# Copyright (c) Polyconseil SAS. All rights reserved.

import sys
import warnings

import pkg_resources

__version__ = pkg_resources.get_distribution('grocker').version
__copyright__ = '2015, Polyconseil'


class GrockerDeprecationWarning(Warning):
    pass


if tuple(sys.version_info[:2]) in ((3, 5)):
    warnings.warn(
        "Support for 3.5 will be dropped in next major version",
        category=GrockerDeprecationWarning,
    )

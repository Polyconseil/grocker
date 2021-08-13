# Copyright (c) Polyconseil SAS. All rights reserved.

import sys
import warnings

try:
    from importlib import metadata
except ImportError:
    # Python<3.8: use importlib-metadata package
    import importlib_metadata as metadata  # type: ignore

__version__ = metadata.version('grocker')
__copyright__ = '2015, Polyconseil'


class GrockerDeprecationWarning(Warning):
    pass


if tuple(sys.version_info[:2]) in ((3, 5)):
    warnings.warn(
        "Support for 3.5 will be dropped in next major version",
        category=GrockerDeprecationWarning,
    )

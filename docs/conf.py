import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from blease.doc.sphinxbaseconf import *

from grocker import __version__


project = u"Grocker"
version = __version__
release = version

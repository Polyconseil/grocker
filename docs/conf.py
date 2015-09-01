import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grocker import __version__, __copyright__

copyright = __copyright__
project = "Grocker"
version = __version__
release = version

extensions = [
    'sphinx.ext.graphviz',
]

master_doc = 'index'
graphviz_output_format = "svg"

html_theme = 'sphinx_rtd_theme'
html_context = {
    'display_github': True,
    'github_user': 'Polyconseil',
    'github_repo': 'grocker',
    'github_version': 'master/',
    'conf_py_path': '',
}

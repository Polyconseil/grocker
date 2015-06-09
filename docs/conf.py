import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from grocker import __version__
from sphinx.builders.html import StandaloneHTMLBuilder

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.extlinks',
    'sphinx.ext.graphviz',
]

graphviz_output_format = "svg"
extlinks = {'trac': ('http://tracker.autolib.polyconseil.fr/ticket/%s', '#')}
source_suffix = '.rst'
master_doc = 'index'
copyright = "2015, Polyconseil"
project = "Grocker"
version = __version__
release = version
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'

# Prefer png to svg for images
image_types = list(StandaloneHTMLBuilder.supported_image_types)
image_types.remove('image/png')
StandaloneHTMLBuilder.supported_image_types = ['image/png'] + image_types

html_context = {
    'display_github' : True,
    'github_user' : 'Polyconseil',
    'github_repo' : 'stub',
    'github_version': 'master/',
    'conf_py_path': 'docs/',
}

intersphinx_mapping = {}
html_context['github_repo'] = 'grocker'
html_context['conf_py_path'] = ''

from grocker import __version__, __copyright__

copyright = __copyright__
project = "Grocker"
version = __version__
release = version

master_doc = 'index'

html_theme = 'sphinx_rtd_theme'
html_context = {
    'display_github': True,
    'github_user': 'Polyconseil',
    'github_repo': 'grocker',
    'github_version': 'master/',
    'conf_py_path': 'docs/',
}

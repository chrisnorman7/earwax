"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import os
import sys
from subprocess import check_output
from typing import List

sys.path.insert(0, os.path.abspath('.'))

sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------


project = 'Earwax'
copyright = '2020, Chris Norman'
author = 'Chris Norman'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib.apidoc',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path: List[str] = ['_static']

apidoc_module_dir: str = os.path.abspath('../../earwax')
apidoc_excluded_paths: List[str] = ['tests', 'cmd/blank_game.py']
apidoc_separate_modules: bool = True
autodoc_mock_imports: List[str] = []


def setup(app):
    """Add extra files."""
    app.add_css_file('custom.css')
    app.add_js_file('custom.js')
    app.add_js_file(
        'https://cdn.jsdelivr.net/npm/clipboard@1/dist/clipboard.min.js'
    )


master_doc = 'index'

version: str = check_output(
    ['git', 'describe', '--abbrev=1', '--always', '--tags']
).decode().strip()

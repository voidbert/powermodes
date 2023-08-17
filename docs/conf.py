# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Get project information from pyproject.toml
from datetime import datetime
from tomllib import load

with open('../pyproject.toml', 'rb') as file:
    pyproject = load(file)['project']

project = pyproject['name']
author = pyproject['authors'][0]['name']
copyright = f'{datetime.now().year}, {author}'
version = release = pyproject['version']

# Autodoc path to modules
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc']

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

add_module_names = False
maximum_signature_line_length=1 # Force one line per function paramater

# Options for HTML output

html_theme = 'bizstyle'
html_theme_options = {
    'sidebarwidth': '20em'
}

html_static_path = ['_static']

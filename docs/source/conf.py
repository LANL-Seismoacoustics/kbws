# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath('../../'))
from kbws import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'KBWS'
copyright = '2025, Jonathan MacCarthy'
author = 'Jonathan MacCarthy'
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]
autosummary_generate = False
suppress_warnings = ["myst.header"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_book_theme"
html_static_path = ['_static']
html_css_files = [
    'css/custom.css',
]
html_theme_options = {
    "home_page_in_toc": True,
    "repository_url": "https://github.com/LANL-seismoacoustics/kbws",
    "use_repository_button": True,
    "show_navbar_depth": 2,
    "use_fullscreen_button": False,
    "logo": {
        "image_light": "_static/LANL Logo Ultramarine.png",
        "image_dark": "_static/LANL Logo White.png",
    }
}
html_favicon = "_static/LANL Logo Ultramarine globe.png"

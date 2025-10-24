# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('../..')) # Apunta a la carpeta raíz 'Budget-Tool'

project = 'Budget Tool Phase II'
copyright = '2025, Cristian Zambrano'
author = 'Cristian Zambrano'
release = '2025'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Para importar documentación desde docstrings
    'sphinx.ext.viewcode',     # Para añadir enlaces al código fuente
    'sphinx.ext.napoleon',     # Para entender docstrings estilo Google/NumPy
    'sphinx_rtd_theme',        # El tema que instalamos
]

templates_path = ['_templates']
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

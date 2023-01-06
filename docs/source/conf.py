# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ethsim'
copyright = '2023, Ferenc Beres, Istvan Andras Seres, Domokos Miklos Kelen'
author = 'Ferenc Beres, Istvan Andras Seres, Domokos Miklos Kelen'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
'recommonmark',
'sphinx_markdown_tables',
'sphinx.ext.duration',
'sphinx.ext.doctest',
'sphinx.ext.autodoc',
'sphinx.ext.autosummary',
'sphinx.ext.todo',
'sphinx.ext.coverage',
'sphinx.ext.imgmath',
'sphinx.ext.viewcode',
'sphinx.ext.napoleon',
'sphinx_rtd_theme',
'sphinx.ext.mathjax',
'sphinx.ext.viewcode',
'sphinx.ext.inheritance_diagram',
'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
master_doc = 'index'

# NOTE: update path to see source code
napoleon_use_param = True
import sys, os
source_dir = os.path.join(os.path.abspath(os.pardir), "..", "python")
print(source_dir)
sys.path.insert(0, source_dir)

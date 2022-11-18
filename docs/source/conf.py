# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ethsim'
copyright = '2022, Ferenc Beres, Istvan Andras Seres, Domokos Miklos Kelen'
author = 'Ferenc Beres, Istvan Andras Seres, Domokos Miklos Kelen'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
'recommonmark',
'sphinx_markdown_tables',
'sphinx.ext.autodoc',
'sphinx.ext.todo',
'sphinx.ext.coverage',
'sphinx.ext.imgmath',
'sphinx.ext.viewcode',
'sphinx.ext.napoleon',
"sphinx_rtd_theme",
]

templates_path = ['_templates']
exclude_patterns = []

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown',
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
master_doc = 'index'
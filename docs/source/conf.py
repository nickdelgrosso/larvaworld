


'''
import inspect
print('larvaworld')
print(inspect.getmembers(larvaworld, inspect.ismodule))
print('larvaworld.cli')
print(inspect.getmembers(larvaworld.cli, inspect.ismodule))
print('larvaworld.lib')
print(inspect.getmembers(larvaworld.lib, inspect.ismodule))
print('larvaworld.lib.aux')
print(inspect.getmembers(larvaworld.lib.aux, inspect.ismodule))
print('larvaworld.lib.param')
print(inspect.getmembers(larvaworld.lib.param, inspect.ismodule))
'''



import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../../src')) # or "../../src
sys.path.append(os.path.abspath('sphinxext'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:


# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

# project = 'larvaworld'
# copyright = '2023, Panagiotis Sakagiannis'
# author = 'Panagiotis Sakagiannis'
# The short X.Y version
# version = ''
# The full version, including alpha/beta/rc tags
# release = ''

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # automatically generate documentation for modules
    "sphinx.ext.napoleon",  # to read Google-style or Numpy-style docstrings
    "sphinx.ext.viewcode",  # to allow vieing the source code in the web page
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
    'sphinx.ext.extlinks',
    'sphinx.ext.graphviz',
    "autodocsumm",  # to generate tables of functions, attributes, methods, etc.
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = []

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = 'en'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'friendly'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# don't include docstrings from the parent class
autodoc_inherit_docstrings = False
# Show types only in descriptions, not in signatures
autodoc_typehints = "description"


# Import the package to document:
import larvaworld
#print(larvaworld.__path__)

from gendocs import Generator
gen = Generator()
gen.DocumentPackages(larvaworld,
                     index_base='../index_base.rst',
                     showprivate=True
                    )
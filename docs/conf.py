# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

from pytest_pyppeteer import __version__

sys.path.insert(0, os.path.abspath("../src/pytest_pyppeteer"))

# -- Project information -----------------------------------------------------

project = "pytest-pyppeteer"
copyright = "2020-2022, Yao Meng"
author = "Yao Meng"

# The full version, including alpha/beta/rc tags
version = __version__
release = version

language = "en"

# -- General configuration ---------------------------------------------------

autodoc_member_order = "bysource"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# This value contains a list of modules to be mocked up.
# This is useful when some external dependencies are not met at build time
# and break the building process. You may only specify the root package of
# the dependencies themselves and omit the sub-modules.
autodoc_mock_imports = ["pytest", "_pytest"]

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = False

# The style name to use for Pygments highlighting of source code.
# If not set, either the theme’s default style or 'sphinx' is selected
# for HTML output.
pygments_style = "sphinx"

intersphinx_mapping = {"python": ("https://docs.python.org/3.7", None)}


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_context = {
    "display_github": True,
    "github_user": "luizyao",
    "github_repo": "pytest-pyppeteer",
    "github_version": "dev/docs/",
}

html_theme_options = {"page_width": "80%"}

"""Sphinx configuration for the qrt docs (Sphinx + MyST)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

project = "qrt"
copyright = "2026, Iman Karimi"
author = "Iman Karimi"

extensions = [
    "myst_parser",
    "autodoc2",
    "sphinx_copybutton",
    "sphinx.ext.napoleon",
]

# -- napoleon -----------------------------------------------------------------
# Docstrings are Google-style; napoleon's converters are reused (via the
# custom autodoc2 docstring parser below) to turn Args/Returns/etc. sections
# into field-list syntax that MyST's `fieldlist` extension can render.
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_use_param = True
napoleon_use_rtype = True

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst",
}

myst_enable_extensions = [
    "fieldlist",
    "colon_fence",
    "deflist",
]

# -- autodoc2 ----------------------------------------------------------------
# qrt.feat.talib / qrt.feat.pandas_ta build their indicator functions at
# runtime via module-level __getattr__, so autodoc2's static analysis can't
# see them as real attributes -- only their module docstrings are rendered,
# matching the previous quartodoc setup (which used `members: []` for the
# same reason).
autodoc2_packages = [
    "../qrt",
]
autodoc2_render_plugin = "myst"
autodoc2_output_dir = "apidocs"
autodoc2_hidden_objects = ["private", "dunder", "inherited"]
# Run every docstring through napoleon (Google/NumPy -> field-list) before
# MyST renders it -- see docs/docstring_parser.py.
autodoc2_docstring_parser_regexes = [
    (r".*", "docstring_parser"),
]

# -- HTML output --------------------------------------------------------------
html_theme = "pydata_sphinx_theme"
html_title = "qrt — Quant Research Tools"

html_theme_options = {
    "github_url": "https://github.com/quantbert/qrt",
    "navigation_with_keys": True,
    "show_toc_level": 2,
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "header_links_before_dropdown": 4,
}

html_context = {
    "default_mode": "auto",
}

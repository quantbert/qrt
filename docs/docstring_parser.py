"""Custom autodoc2 docstring parser that runs Google/NumPy-style docstrings
through ``sphinx.ext.napoleon`` before handing them to MyST.

``sphinx-autodoc2`` has no built-in support for Google/NumPy docstring
sections (``Args:``, ``Returns:``, ...) -- it only chooses between
plain ``rst``/``myst`` body syntax. Napoleon's ``GoogleDocstring``/
``NumpyDocstring`` converters rewrite those sections into Sphinx field-list
syntax (``:param x:``, ``:returns:``), which MyST's ``fieldlist`` extension
then renders as a proper parameter list.

See: https://github.com/sphinx-extensions2/sphinx-autodoc2/issues/33
"""

from __future__ import annotations

from docutils import nodes
from myst_parser.parsers.sphinx_ import MystParser
from sphinx.ext.napoleon import docstring


class NapoleonParser(MystParser):
    def parse(self, inputstring: str, document: nodes.document) -> None:
        config = document.settings.env.config
        parsed = str(
            docstring.GoogleDocstring(
                str(docstring.NumpyDocstring(inputstring, config)), config
            )
        )
        return super().parse(parsed, document)


Parser = NapoleonParser

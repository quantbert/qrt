"""Regenerate .pyi stubs for the dynamic feature wrappers (IDE support).

``qrt.feature.talib`` and ``qrt.feature.pandas_ta`` create their indicator
functions at runtime via module-level ``__getattr__``, which static
analyzers (Pylance, mypy) cannot see. This script writes type stubs with
real signatures and docstrings next to those modules so IDEs can offer
autocomplete and hover docs.

Usage:
    uv run python tools/gen_feature_stubs.py

Rerun after upgrading ta-lib or pandas-ta-classic.

Note: both upstreams have their own stub generators. ta-lib ships
``talib/_ta_lib.pyi`` and ``talib/abstract.pyi`` in the wheel (covering
direct ``import talib`` usage, not our wrapper namespace). pandas-ta-classic
has ``tools/gen_core_stub.py`` on main, but as of 0.6.52 the generated
``core.pyi`` is not shipped in the release -- once it is, the ``df.ta``
accessor gets IDE support natively and this script could reuse it.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pandas_ta_classic as pta
import talib
from talib import abstract

FEATURE_DIR = Path(__file__).resolve().parents[1] / "qrt" / "feature"

HEADER = '''"""Auto-generated stubs for the dynamic indicator wrappers (IDE support).

Do not edit by hand. Regenerate with:

    uv run python tools/gen_feature_stubs.py
"""

from typing import Any

import pandas as pd

'''

# Price-series parameters supplied automatically from the OHLCV frame.
_PRICE_PARAMS = {"open_", "open", "high", "low", "close", "volume"}


def _fmt_doc(doc: str | None) -> str:
    """Render a function body containing the docstring, indented one level."""
    if not doc or not doc.strip():
        return "    ...\n"
    text = doc.replace("\\", "\\\\").replace('"""', "'''").strip("\n")
    lines = text.splitlines()
    body = "\n".join(("    " + line).rstrip() for line in lines)
    return f'    """\n{body}\n    """\n    ...\n'


def _fmt_default(value: object) -> str:
    rep = repr(value)
    # Guard against non-literal reprs (objects, functions, ...).
    return rep if all(c not in rep for c in "<>") else "..."


def gen_talib_stub() -> str:
    chunks = [HEADER]
    for name in sorted(talib.get_functions()):
        fn = abstract.Function(name)
        params = "".join(
            f", {pname}: Any = {_fmt_default(default)}"
            for pname, default in fn.parameters.items()
        )
        doc = getattr(talib, name).__doc__  # per-indicator docstring
        chunks.append(
            f"def {name}(data: pd.Series | pd.DataFrame{params}"
            ") -> pd.Series | pd.DataFrame:\n" + _fmt_doc(doc)
        )
    return "\n".join(chunks)


def gen_pandas_ta_stub() -> str:
    names = sorted({n for group in pta.Category.values() for n in group})
    chunks = [HEADER]
    for name in names:
        fn = getattr(pta, name, None)
        if fn is None or not callable(fn):
            continue
        parts = []
        for pname, param in inspect.signature(fn).parameters.items():
            if pname in _PRICE_PARAMS or param.kind is param.VAR_KEYWORD:
                continue
            if param.default is param.empty:
                parts.append(f", {pname}: Any = ...")
            else:
                parts.append(f", {pname}: Any = {_fmt_default(param.default)}")
        chunks.append(
            f"def {name}(data: pd.Series | pd.DataFrame{''.join(parts)}, **kwargs: Any"
            ") -> pd.Series | pd.DataFrame:\n" + _fmt_doc(fn.__doc__)
        )
    return "\n".join(chunks)


def main() -> None:
    for filename, content in [
        ("talib.pyi", gen_talib_stub()),
        ("pandas_ta.pyi", gen_pandas_ta_stub()),
    ]:
        path = FEATURE_DIR / filename
        path.write_text(content)
        print(f"wrote {path} ({content.count('def ')} functions)")


if __name__ == "__main__":
    main()

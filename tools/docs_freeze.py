"""Invalidate Quarto freeze output when shared notebook inputs change."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FREEZE_DIR = ROOT / "docs" / "_freeze"
STATE_FILE = ROOT / "docs" / ".qrt-runtime.sha256"
RUNTIME_INPUTS = (
    ROOT / "qrt",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
    ROOT / "demo-requirements.yml",
)


def runtime_fingerprint() -> str:
    """Hash package code, bundled data, and environment definitions."""
    digest = hashlib.sha256()
    files = sorted(
        path
        for runtime_input in RUNTIME_INPUTS
        for path in (
            runtime_input.rglob("*") if runtime_input.is_dir() else (runtime_input,)
        )
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )

    for path in files:
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def prepare(*, force: bool) -> None:
    """Remove frozen computations when shared runtime inputs changed."""
    fingerprint = runtime_fingerprint()
    previous = STATE_FILE.read_text().strip() if STATE_FILE.exists() else None
    if force or fingerprint != previous:
        reason = "refresh requested" if force else "shared runtime inputs changed"
        print(f"Clearing Quarto freeze cache: {reason}.")
        shutil.rmtree(FREEZE_DIR, ignore_errors=True)
    else:
        print("Shared runtime inputs unchanged; preserving Quarto freeze cache.")


def record() -> None:
    """Record inputs only after Quarto completes a successful render."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(f"{runtime_fingerprint()}\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("record")
    args = parser.parse_args()

    if args.command == "prepare":
        prepare(force=args.force)
    else:
        record()


if __name__ == "__main__":
    main()
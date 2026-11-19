"""Additive reproducible tree hashing for frozen-manifest equivalence checks.

The legacy :func:`src.bedrock.provenance.hash_tree` remains unchanged.  This module uses the same
sorted ``(relative POSIX path, file hash)`` representation while excluding Python bytecode and
``__pycache__`` contents, which are interpreter artifacts rather than protocol inputs.
"""

from __future__ import annotations

from pathlib import Path

from .provenance import hash_file, hash_json


def hash_tree_tracked(root: str | Path, pattern: str = "**/*") -> str:
    """Hash a tree like legacy ``hash_tree``, excluding ``__pycache__`` and ``*.pyc`` files."""
    root = Path(root)
    entries = sorted(
        (relative.as_posix(), hash_file(path))
        for path in root.glob(pattern)
        if path.is_file()
        for relative in [path.relative_to(root)]
        if "__pycache__" not in relative.parts and path.suffix != ".pyc"
    )
    return hash_json(entries)


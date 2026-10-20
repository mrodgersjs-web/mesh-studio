"""Tests for packaging invariants that have silently drifted before.

These assert real expected values: the package version must match the
pyproject metadata, and the PEP 561 marker must ship with the package.
Plain regex parsing keeps this runnable on every supported Python.
"""
from __future__ import annotations

import re
from pathlib import Path

import rig_mesh

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = (REPO_ROOT / "pyproject.toml").read_text()


def test_dunder_version_matches_pyproject():
    match = re.search(r'^version = "([^"]+)"', PYPROJECT, re.MULTILINE)
    assert match is not None
    assert rig_mesh.__version__ == match.group(1) == "1.1.0"


def test_py_typed_marker_exists_in_package():
    assert (REPO_ROOT / "src" / "rig_mesh" / "py.typed").is_file()


def test_py_typed_is_declared_as_package_data():
    assert 'rig_mesh = ["py.typed"]' in PYPROJECT

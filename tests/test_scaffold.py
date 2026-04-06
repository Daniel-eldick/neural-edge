"""Smoke test to verify project scaffold is set up correctly."""

import importlib


def test_project_imports() -> None:
    """Verify all src packages are importable."""
    packages = [
        "src",
        "src.strategies",
        "src.sensory",
        "src.signals",
        "src.autoresearch",
        "src.adapters",
        "src.core",
    ]
    for pkg in packages:
        importlib.import_module(pkg)

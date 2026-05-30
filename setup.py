#!/usr/bin/env python3
"""
Minimal setup.py shim for backward compatibility.

All project metadata and configuration is now in pyproject.toml.
This file is kept only for legacy tools that do not support PEP 517/518.

For modern usage, prefer:
    pip install -e .           # core install
    pip install -e ".[dev]"    # development install
"""

from setuptools import setup

setup()

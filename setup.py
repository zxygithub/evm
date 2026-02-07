#!/usr/bin/env python3
"""Setup script for EVM (Environment Variable Manager)."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="evm-cli",
    version="1.5.0",
    author="EVM Tool",
    author_email="evm@example.com",
    description="A command-line tool for managing environment variables",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zxygithub/evm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        # No external dependencies for core functionality
    ],
    entry_points={
        "console_scripts": [
            "evm=evm.python.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

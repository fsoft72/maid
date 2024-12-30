#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="fsoft-maid",
    version="0.4.6",
    description="Markdown AI Doc creator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Fabio Rotondo",
    author_email="fsoft.devel@gmail.com",
    url="https://github.com/fsoft72/maid",
    license="MIT",
    packages=find_packages(),
    py_modules=["fsoft_maid", "lib.pattern_matcher"],
    entry_points={
        "console_scripts": [
            "maid=fsoft_maid:main",
        ],
    },
    install_requires=[
        # List your dependencies here
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="fsoft-maid",
    version="0.3.5",
    description="Markdown AI Doc creator",
    author="Fabio Rotondo",
    author_email="fsoft.devel@gmail.com",
    url="https://github.com/fsoft72/maid",
    license="MIT",
    packages=find_packages(),
    py_modules=["fsoft_maid"],
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

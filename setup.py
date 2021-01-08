#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools
from zeta import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zeta-cli",  # Replace with your own username
    version=__version__,
    author="Rodrigo Peixoto",
    author_email="rodrigopex@gmail.com",
    description=
    "Zeta cli is a tool to generate files needed by the Zeta project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lucaspeixotot/zeta",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={"console_scripts": ["zeta = zeta.zeta:run"]},
    include_package_data=True,
    install_requires=["pyyaml"])

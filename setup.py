#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ntlm-theft",
    version="0.2.1",
    author="Jacob Wilkin (Greenwolf)",
    description="A tool for generating multiple types of NTLMv2 hash theft files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kasem545/ntlm_theft",
    packages=find_packages(),
    package_data={
        "ntlm_theft": ["templates/**/*"],
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "xlsxwriter",
    ],
    entry_points={
        "console_scripts": [
            "ntlm-theft=ntlm_theft:main",
        ],
    },
)

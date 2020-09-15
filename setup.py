#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "pyyaml",
    "click",
    "tqdm",
    "fileselection>=0.3.2",
    "pydicom",
    "tabulate",
    "requests",
    "factory_boy",
]

setup_requirements = [
    "pytest-runner",
]

test_requirements = ["pytest", "pyyaml", "factory_boy"]

setup(
    author="Sjoerd Kerkstra",
    author_email="sjoerd.kerkstra@radboudumc.nl",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Client and tools for working with the anoymization web API",
    python_requires=">=3.6",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="anonapi",
    name="anonapi",
    packages=find_packages(include=["anonapi", "anonapi.cli"]),
    entry_points={"console_scripts": ["anon = anonapi.cli.entrypoint:cli"]},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/sjoerdk/anonapi",
    version="1.3.0",
    zip_safe=False,
)

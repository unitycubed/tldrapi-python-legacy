# -*- coding: utf-8 -*-
"""setup.py for tldrapi-legacy — Python 2.7 SDK for TLDRapi."""
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="tldrapi-legacy",
    version="0.1.0",
    description=(
        "Python 2.7 legacy SDK for TLDRapi (text summarization API). "
        "For Python 3.8+, use the `tldrapi` package instead."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ehren Biglari",
    author_email="support@unitycubed.dev",
    url="https://github.com/unitycubed/tldrapi-python-legacy",
    license="MIT",
    packages=["tldrapi_legacy"],
    install_requires=[
        # `requests` is the only viable HTTP lib that still supports
        # Python 2.7 out of the box. Pinned to a range that keeps py2
        # wheels installable on stuck-on-2.7 boxes.
        "requests>=2.20.0,<3",
    ],
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,<3.8",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="tldrapi summarize summarization text nlp api sdk legacy python2",
)

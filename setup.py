#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Note: To use the 'upload' functionality of this file, you must:
#   $ pip install twine

import io
import os
import sys
from shutil import rmtree

from setuptools import find_packages, setup, Command

# Package meta-data.
NAME = "pyffdl"
DESCRIPTION = "Fanfiction download script"
URL = "https://github.com/Birion/python-ffdl"
EMAIL = "ondrej.vagner@gmail.com"
AUTHOR = "Birion"
REQUIRES_PYTHON = ">=3.10"
VERSION = None

# What packages are required for this module to be executed?
REQUIRED = [
    "attrs>=22",
    "beautifulsoup4>=4.11",
    "click>=8",
    "cloudscraper>=1",
    "ebooklib>=0.18",
    "furl>=2",
    "html5lib>=1",
    "jinja2>=3",
    "pendulum>=2",
    "pillow>=9.4.0",
    "pycountry>=22",
    "requests>=2.28",
]
DEPENDENCY = []

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.rst' is present in your MANIFEST.in file!
with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, "__version__.py")) as f:
        exec(f.read(), about)
else:
    about["__version__"] = VERSION


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print("\033[1m{0}\033[0m".format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous builds…")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution…")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        # self.status('Uploading the package to PyPi via Twine…')
        # os.system('twine upload dist/*')

        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(about["__version__"]))
        os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=("tests",)),
    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],
    entry_points={"console_scripts": ["pyffdl=pyffdl:cli"]},
    install_requires=REQUIRED,
    dependency_links=DEPENDENCY,
    include_package_data=True,
    license="MIT",
    keywords="fanfiction downloader",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    # $ setup.py publish support.
    cmdclass={"upload": UploadCommand},
)

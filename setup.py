# coding=utf-8

from setuptools import setup

setup(
    name="pyffdl",
    version="0.1.0",
    py_modules=["pyffdl"],
    packages=["ffdl"],
    include_package_data=True,
    url="https://github.com/Birion/python-ffdl",
    license="MIT License",
    author="Birion",
    author_email="ondrej.vagner@gmail.com",
    description="Fanfiction downloader",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6"
    ],
    install_requires=[
        "click",
        "iso639",
        "requests",
        "beautifulsoup4",
        "ebooklib",
        "mako",
        "html5lib",
        "furl"
    ],
    entry_points="""
        [console_scripts]
        pyffdl=pyffdl:cli
    """,
    package_data={
        "": ["title.mako", "style.css"],
    }
)

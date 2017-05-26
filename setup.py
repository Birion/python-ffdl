from setuptools import setup

setup(
    name="pyffdl",
    version="0.2.0",
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
        "click>=6",
        "iso639>=0.1",
        "requests>=2",
        "beautifulsoup4",
        "ebooklib>=0.16",
        "mako>=1",
        "html5lib>0.9999",
        "furl>=1"
    ],
    entry_points="""
        [console_scripts]
        pyffdl=pyffdl:cli
    """,
    package_data={
        "": ["title.mako", "style.css"],
    }
)

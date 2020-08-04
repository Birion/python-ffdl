# python-ffdl
Fanfiction downloader

[![Build Status](https://travis-ci.org/Birion/python-ffdl.svg?branch=master)](https://travis-ci.org/Birion/python-ffdl)

## Installation

`$ pip install git+ssh://git@github.com/Birion/python-ffdl.git@master`

## Usage

### Download a new story

`pyffdl download [--from <URL FILE>] [<URL>[ <URL>[...]]]`

The `html` command downloads a raw list of HTML files and collates them in an ebook.

`pyffdl html --author <NAME> --title <TITLE> [--from <URL FILE>] [<CHAPTER URL>[ <CHAPTER URL>[...]]]`

In `URL_FILE`, you can provide a list of URLs to download, one URL per line. Any lines starting with `#` will be ignored.

### Update an existing story file

`pyffdl.py update [--force] [--backup] <EPUB FILE>`

`--force` option completely redownloads the story, overwriting any changes you may have done to the epub file in the meantime.

`--backup` option saves a copy of the current epub file before downloading any updates into a new file.

## Supported sites

* [adult-fanfiction.org](http://www.adult-fanfiction.org)
* [archiveofourown.org](https://archiveofourown.org)
* [fanfiction.net](https://fanfiction.net)
* [fictionpress.com](https://fictionpress.com)
* [tgstorytime.com](https://tgstorytime.com)
* [tthfanfic.org](https://tthfanfic.org)

## TODO

* better covers
    * by genres?
* actually useful tests
* figure out why the cover page is non-linear in .epub
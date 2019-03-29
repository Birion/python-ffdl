#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

from pathlib import Path
from re import sub, match
from typing import List, Tuple, Union

import attr
from bs4 import BeautifulSoup, Tag
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class HTMLStory(Story):
    chapters: List[str]
    author: str
    title: str

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

        text = BeautifulSoup(page.text, "html5lib")
        text = sub(r"(\n|\r|\s)+", " ", str(text))
        text = sub(r"\s*(</?p>)\s*", r"\1", text)
        text = sub(r"<br/?>", "</p><p>", text)
        text = sub(r"<p>\s*</p>", "", text)

        return clean_text(
            [
                x
                for x in BeautifulSoup(text, "html5lib").find("body")("p")
                if not match(r"^\s*<p>\s*</p>\s*$", str(x))
            ]
        )

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """

        def _parse_url(url: str) -> Tuple[furl, str]:
            _url = furl(url)
            _file = _url.path.segments[-1]
            _name = _file.split(".")[0] if "." in _file else _file
            return _url, _name.capitalize()

        self.metadata.chapters = [_parse_url(x) for x in self.chapters]

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """
        self.metadata.title = self.title
        self.metadata.author.name = self.author
        self.metadata.author.url = None
        self.metadata.language = "English"
        self.url = None

    def make_new_chapter_url(self, url: furl, value: str) -> furl:
        return furl(value)

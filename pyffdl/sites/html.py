import re
from typing import List, Tuple, Optional

import attr
from bs4 import BeautifulSoup  # type: ignore
from furl import furl  # type: ignore
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class HTMLStory(Story):
    chapters: List[str]
    author: str
    title: str

    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        text = BeautifulSoup(response.text, "html5lib")
        text = str(text)

        replacement_strings = [
            (r"(\n|\r|\s)+", " "),
            (r"\s*(</?p>)\s*", r"\1"),
            (r"<br/?>", "</p><p>"),
            (r"<p>\s*</p>", ""),
        ]

        for r, s in replacement_strings:
            text = re.sub(r, s, text)

        return clean_text(
            [
                x
                for x in BeautifulSoup(text, "html5lib").find("body")("p")
                if not re.match(r"^\s*<p>\s*</p>\s*$", str(x))
            ]
        )

    def get_chapters(self) -> None:
        """Gets the number of chapters and the base template for chapter URLs."""  # noqa: D202

        def _parse_url(url: str) -> Tuple[furl, str]:
            _url = furl(url)
            _file = _url.path.segments[-1]
            _name = _file.split(".")[0] if "." in _file else _file
            return _url, _name.capitalize()

        self.metadata.chapters = [_parse_url(x) for x in self.chapters]

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""
        self.metadata.title = self.title
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = self.author
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = None
        self.metadata.language = "English"
        self.url = furl(None)

    def make_new_chapter_url(self, url: furl, value: str) -> Optional[furl]:
        return furl(value)

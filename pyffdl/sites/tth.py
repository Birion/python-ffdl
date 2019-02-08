from datetime import date
from re import compile, sub, match
from typing import Dict, List, Union

import pendulum
from bs4 import BeautifulSoup, Tag
from click import echo
from furl import furl
from requests import Response
import attr
import iso639

from pyffdl.sites.story import Story
from pyffdl.utilities import in_dictionary, turn_into_dictionary
from pyffdl.utilities.misc import clean_text


@attr.s
class Header:
    category = attr.ib()
    author = attr.ib()
    rating = attr.ib()
    chapters = attr.ib(converter=int)
    words = attr.ib(converter=lambda x: int(x.replace(",", "")))
    recs = attr.ib()
    reviews = attr.ib()
    hits = attr.ib()
    published = attr.ib(
        converter=lambda x: pendulum.from_format(
            x, "DD MMM YY", tz=pendulum.local_timezone()
        )
    )
    updated = attr.ib(
        converter=lambda x: pendulum.from_format(
            x, "DD MMM YY", tz=pendulum.local_timezone()
        )
    )
    complete = attr.ib(converter=lambda x: x == "Yes")


@attr.s
class TwistingTheHellmouthStory(Story):
    _chapter_select: str = attr.ib(init=False, default="select#chapnav option")
    _story_id: str = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._story_id = match(
            r"Story-(?P<story>\d+)(-\d+)?", self.url.path.segments[0]
        ).group("story")

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        soup = BeautifulSoup(page.content, "html5lib")
        div = soup.find("div", id="storyinnerbody")
        empty_div = div.find("div", style="clear:both;")
        empty_div.extract()
        raw_text = clean_text(div.contents)
        _clean_text = sub(r"\s*(<br/?>){2,}\s*", "</p><p>", raw_text) + "</p>"
        _clean_text = sub(r"<p></p>", "", _clean_text)
        if _clean_text.startswith("<"):
            _clean_text = sub(r"(</h\d>)\s*([^<])", r"\1<p>\2", _clean_text)
        else:
            _clean_text = "<p>" + _clean_text

        return _clean_text

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        _header = self._main_page.find(
            "div", class_="storysummary formbody defaultcolors"
        )
        _author = self._main_page.find("a", href=compile(r"^/AuthorStories"))
        _data = Header(
            *[
                sub(r"\xa0", " ", x.text.strip())
                for x in _header.table.find_all("tr")[-1].find_all("td")
            ]
        )

        self._metadata.title = self._main_page.find("h2").string.strip()
        if not self._metadata.chapters:
            self._metadata.chapters = [self._metadata.title]
        self._metadata.author.name = _author.text
        self._metadata.author.url = self.url.copy().set(path=_author["href"])
        self._metadata.complete = _data.complete
        self._metadata.rating = _data.rating
        self._metadata.updated = _data.updated
        self._metadata.published = _data.published
        if self._metadata.updated == self._metadata.published:
            self._metadata.updated = None
        self._metadata.language = iso639.to_name(self._main_page.html["lang"])
        self._metadata.words = _data.words
        self._metadata.summary = _header.find_all("p")[-1].text
        self._metadata.genres = None
        self._metadata.category = _data.category
        self._metadata.tags = None

        self._metadata.characters = {"couples": None, "singles": None}

        clean_title = sub(rf"{self.ILLEGAL_CHARACTERS}", "_", self._metadata.title)
        self._filename = f"{self._metadata.author.name} - {clean_title}.epub"

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[0] = f"Story-{self._story_id}-{value}"
        return url

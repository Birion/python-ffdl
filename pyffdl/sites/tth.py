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
from pyffdl.utilities import turn_into_dictionary
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


@attr.s(auto_attribs=True)
class TwistingTheHellmouthStory(Story):
    chapter_select: str = attr.ib(init=False, default="select#chapnav option")
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
        return clean_text(div.contents)

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        _header = self.main_page.find(
            "div", class_="storysummary formbody defaultcolors"
        )
        _author = self.main_page.find("a", href=compile(r"^/AuthorStories"))
        _data = Header(
            *[
                sub(r"\xa0", " ", x.text.strip())
                for x in _header.table.find_all("tr")[-1].find_all("td")
            ]
        )

        self.metadata.title = self.main_page.find("h2").string.strip()
        if not self.metadata.chapters:
            self.metadata.chapters = [self.metadata.title]
        self.metadata.author.name = _author.text
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.complete = _data.complete
        self.metadata.rating = _data.rating
        self.metadata.updated = _data.updated
        self.metadata.published = _data.published
        if self.metadata.updated == self.metadata.published:
            self.metadata.updated = None
        self.metadata.language = iso639.to_name(self.main_page.html["lang"])
        self.metadata.words = _data.words
        self.metadata.summary = _header.find_all("p")[-1].text
        self.metadata.genres = None
        self.metadata.category = _data.category
        self.metadata.tags = None

        self.metadata.characters = {"couples": None, "singles": None}

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[0] = f"Story-{self._story_id}-{value}"
        return url

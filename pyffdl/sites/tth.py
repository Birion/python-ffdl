import re
from typing import Optional

import attr
import iso639  # type: ignore
import pendulum  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from bs4.element import Tag  # type: ignore
from furl import furl  # type: ignore
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text


def number_cleanup(count: str) -> int:
    return int(count.replace(",", ""))


def date_cleanup(date: str) -> pendulum.DateTime:
    return pendulum.from_format(date, "DD MMM YY", tz="UTC")


def completion_check(status: str) -> bool:
    return status == "Yes"


@attr.s
class Header:
    category = attr.ib()
    author = attr.ib()
    rating = attr.ib()
    chapters = attr.ib(converter=int)
    words = attr.ib(converter=number_cleanup)
    recs = attr.ib()  # noqa: unused-variable
    reviews = attr.ib()  # noqa: unused-variable
    hits = attr.ib()  # noqa: unused-variable
    published = attr.ib(converter=date_cleanup)
    updated = attr.ib(converter=date_cleanup)
    complete = attr.ib(converter=completion_check)


@attr.s(auto_attribs=True)
class TwistingTheHellmouthStory(Story):
    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        soup = BeautifulSoup(response.content, "html5lib")
        div = soup.find("div", id="storyinnerbody")
        empty_div = div.find("div", style="clear:both;")
        empty_div.extract()
        return clean_text(div.contents)

    @staticmethod
    def chapter_parser(value: Tag) -> str:
        return re.sub(r"\d+\.\s+", "", value.text)

    @property
    def select(self) -> str:
        return "select#chapnav option"

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""
        _header = self.page.find("div", class_="storysummary formbody defaultcolors")
        _author = self.page.find("a", href=re.compile(r"^/AuthorStories"))
        _data = Header(
            *[
                re.sub(r"\xa0", " ", x.text.strip())
                for x in _header.table.find_all("tr")[-1].find_all("td")
            ]
        )

        self.metadata.title = self.page.find("h2").string.strip()
        if not self.metadata.chapters:
            self.metadata.chapters = [self.metadata.title]
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = _author.text
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.complete = _data.complete
        self.metadata.rating = _data.rating
        self.metadata.updated = _data.updated
        self.metadata.published = _data.published
        if self.metadata.updated == self.metadata.published:
            self.metadata.updated = None
        self.metadata.language = iso639.to_name(self.page.html["lang"])
        self.metadata.words = _data.words
        self.metadata.summary = _header.find_all("p")[-1].text
        self.metadata.category = _data.category

        self.metadata.characters = {"couples": None, "singles": None}

    def make_new_chapter_url(self, url: furl, value: str) -> Optional[furl]:
        story = re.match(r"Story-(?P<story>\d+)(-\d+)?", self.url.path.segments[0])
        if story:
            story_id = story.group("story")
            url.path.segments[0] = f"Story-{story_id}-{value}"
            return url
        return None

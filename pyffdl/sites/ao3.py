from datetime import date
from re import compile, sub
from typing import Dict, List

import pendulum
from bs4 import BeautifulSoup, Tag
from click import echo
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities import in_dictionary, turn_into_dictionary


class ArchiveOfOurOwnStory(Story):
    def __init__(self, url: str) -> None:
        super(ArchiveOfOurOwnStory, self).__init__(url)

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        raw_text = "".join(
            sub(r"\s+", " ", str(x).strip())
            for x in BeautifulSoup(page.content, "html5lib")
            .find("div", class_="userstuff module")
            .find("p")
            .contents
        )
        clean_text = sub("<br/><br/>", "</p><p>", raw_text)
        return "<p>" + clean_text + "</p>"

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page.find("select", id="selected_id")("option")

        if list_of_chapters:
            self.metadata.chapters = [
                (int(x["value"]), sub(r"^\d+\.\s+", "", x.text))
                for x in list_of_chapters
            ]
        else:
            self.metadata.chapters = [self.metadata.title]

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def find_with_class(cls: str, elem: str = "dd") -> str:
            _header = self.main_page.find("dl", class_="work meta group")
            _strings = "".join(x for x in _header.find(elem, class_=cls).stripped_strings)
            return _strings

        _author = self.main_page.find("a", rel="author")

        self.metadata.title = self.main_page.find("h2", class_="title heading").string.strip()
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.rating = find_with_class("rating")
        self.metadata.complete = int(find_with_class("chapters").split("/")[0]) == len(self.metadata.chapters)
        self.metadata.updated = pendulum.parse(find_with_class("status")) if self.metadata.complete else None
        self.metadata.published = pendulum.parse(find_with_class("published"))
        self.metadata.language = find_with_class("language")
        self.metadata.words = int(find_with_class("words"))
        self.metadata.summary = None
        self.metadata.genres = None
        self.metadata.category = find_with_class("fandom")

        characters = [x.strip() for x in find_with_class("character").split(",")]
        couples = [x.split("/") for x in find_with_class("relationship").split(",")]
        _not_singles = {character for couple in couples for character in couple}

        self.metadata.characters = {
            "couples": couples,
            "singles": [character for character in characters if character not in _not_singles]
        }

        clean_title = sub(rf"{self.ILLEGAL_CHARACTERS}", "_", self.metadata.title)
        self.filename = f"{self.metadata.author.name} - {clean_title}.epub"

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-1] = value
        return url

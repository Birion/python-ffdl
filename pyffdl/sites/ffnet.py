from datetime import date
from re import compile, sub
from typing import Dict, List

import attr
import pendulum
from bs4 import BeautifulSoup, Tag
from click import echo
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities import turn_into_dictionary
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class FanFictionNetStory(Story):
    chapter_select: str = attr.ib(init=False, default="span select#chap_select option")

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        soup = BeautifulSoup(page.content, "html5lib").select_one("div#storytext")
        return clean_text(soup.contents)

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def check_date(timestamp: int) -> date:
            if not timestamp:
                return pendulum.from_timestamp(0, "local")
            return pendulum.from_timestamp(timestamp, "local")

        def parse_characters(characters: str) -> Dict[str, List[str]]:
            out_couples = []
            out_singles = []
            couples = compile(r"\[[^[]+\]")
            character_couples = [x for x in couples.finditer(characters)]

            if character_couples:
                num_couples = len(character_couples)
                for couple in character_couples:
                    out_couples.append(couple.group()[1:-1].split(", "))
                for i in range(-1, -num_couples - 1, -1):
                    match = character_couples[i]
                    characters = characters.replace(match.group(), "").strip()
            if characters:
                out_singles = characters.split(", ")
            return {"couples": out_couples, "singles": out_singles}

        _header = self.main_page.find(id="profile_top")
        _author = _header.find("a", href=compile(r"^/u/\d+/"))
        _data = turn_into_dictionary(
            [
                x.strip()
                for x in " ".join(
                    str(x) for x in _header.find(class_="xgray").contents
                ).split(" - ")
            ]
        )

        if "Characters" in _data.keys():
            _data["Characters"] = parse_characters(", ".join(_data["Characters"]))

        time_pattern = compile(r'xutime="(\d+)"')

        published = _data.get("Published")
        updated = _data.get("Updated")
        rating = _data.get("Rated")

        self.metadata.title = _header.find("b").string
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.summary = _header.find("div", class_="xcontrast_txt").string
        if rating:
            self.metadata.rating = BeautifulSoup(rating, "html5lib").find("a").string
        self.metadata.category = (
            self.main_page.find(id="pre_story_links").find("a").string
        )
        self.metadata.genres = _data.get("Genres")
        self.metadata.characters = _data.get("Characters")
        self.metadata.words = _data.get("Words")
        if published:
            published = time_pattern.search(published).group(1)
            self.metadata.published = check_date(int(published))
        if updated:
            updated = time_pattern.search(updated).group(1)
            self.metadata.updated = check_date(int(updated))
        else:
            self.metadata.updated = None
        self.metadata.language = _data.get("Language")
        self.metadata.complete = _data.get("Status")

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-2] = value
        return url

from datetime import date
from re import compile, sub
from typing import Dict, List, Union

import attr
import pendulum
from bs4 import BeautifulSoup
from furl import furl
from pendulum import DateTime
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

        # noinspection PyTypeChecker
        def check_date(data: Dict[str, Union[str, int]], key: str) -> Union[DateTime, None]:
            timestamp = data.get(key)
            if timestamp:
                return pendulum.from_timestamp(timestamp, "UTC")
            else:
                return None

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

        header = self.main_page.find(id="profile_top")
        _author = header.find("a", href=compile(r"^/u/\d+/"))
        tags = [
            x.string.strip() if x.name != "span" else x["data-xutime"]
            for x in header.find(class_="xgray").children
        ]
        _data = turn_into_dictionary(sub(r"\s+", " ", " ".join(tags)).split(" - "))

        if "Characters" in _data.keys():
            _data["Characters"] = parse_characters(", ".join(_data["Characters"]))

        self.metadata.title = header.find("b").string
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.summary = header.find("div", class_="xcontrast_txt").string
        self.metadata.rating = _data.get("Rated")
        self.metadata.category = (
            self.main_page.find(id="pre_story_links").find("a").string
        )
        self.metadata.genres = _data.get("Genres")
        self.metadata.characters = _data.get("Characters")
        self.metadata.words = _data.get("Words")
        self.metadata.published = check_date(_data, "Published")
        self.metadata.updated = check_date(_data, "Updated")
        self.metadata.language = _data.get("Language")
        self.metadata.complete = _data.get("Status")

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-2] = value
        return url

from datetime import date
from re import compile, sub
from typing import Dict, List

import pendulum
from bs4 import BeautifulSoup
from click import echo
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities import in_dictionary, turn_into_dictionary


class FanFictionNetStory(Story):
    def __init__(self, url: str) -> None:
        super(FanFictionNetStory, self).__init__(url)

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        return "".join(
            [
                sub(r"\s+", " ", str(x).strip())
                for x in BeautifulSoup(page.content, "html5lib")
                .find("div", class_="storytext")
                .contents
            ]
        )

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page.find("select", id="chap_select")("option")

        if list_of_chapters:
            self.metadata.chapters = [
                sub(r"\d+\. ", "", x.text) for x in list_of_chapters
            ]
        else:
            self.metadata.chapters = [self.metadata.title]

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
            _data["Characters"] = ", ".join(_data["Characters"])
            echo(_data)
            _data["Characters"] = parse_characters(_data["Characters"])
        else:
            echo(_data)

        time_pattern = compile(r'xutime="(\d+)"')

        published = in_dictionary(_data, "Published")
        updated = in_dictionary(_data, "Updated")
        rating = in_dictionary(_data, "Rated")

        self.metadata.title = _header.find("b").string
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.summary = _header.find("div", class_="xcontrast_txt").string
        if rating:
            self.metadata.rating = BeautifulSoup(rating, "html5lib").find("a").string
        self.metadata.category = (
            self.main_page.find(id="pre_story_links").find("a").string
        )
        self.metadata.genres = in_dictionary(_data, "Genres")
        self.metadata.characters = in_dictionary(_data, "Characters")
        self.metadata.words = in_dictionary(_data, "Words")
        if published:
            published = time_pattern.search(published).group(1)
            self.metadata.published = check_date(int(published))
        if updated:
            updated = time_pattern.search(updated).group(1)
            self.metadata.updated = check_date(int(updated))
        else:
            self.metadata.updated = None
        self.metadata.language = in_dictionary(_data, "Language")
        self.metadata.complete = in_dictionary(_data, "Status")

        clean_title = sub(rf"{self.ILLEGAL_CHARACTERS}", "_", self.metadata.title)
        self.filename = f"{self.metadata.author.name} - {clean_title}.epub"

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-2] = value
        return url

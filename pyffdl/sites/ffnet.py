import re
from typing import Dict, List, Union, Tuple, Optional

import attr
import pycountry
import pendulum
from bs4 import BeautifulSoup
from bs4.element import Tag
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text, split

Couple = List[str]
Characters = Dict[str, Union[List[str], List[Couple]]]
Genres = List[str]
ParseResult = Tuple[str, Union[str, int, Genres, Characters]]


def turn_into_dictionary(input_data: List[str]) -> Dict[str, Union[str, int, Genres, Characters]]:
    """Transform a list with fic data into a dictionary."""

    def parse_data(datum: List[str]) -> Optional[ParseResult]:
        val: Optional[str]
        key, *_ = datum
        val = _[0] if _ else None

        keys = [
            "Rated",
            "Language",
            "Genres",
            "Characters",
            "Words",
            "Published",
            "Updated",
            "Status",
        ]
        genres = [
            "Adventure",
            "Angst",
            "Comfort",
            "Crime",
            "Drama",
            "Family",
            "Fantasy",
            "Friendship",
            "General",
            "Horror",
            "Humor",
            "Hurt",
            "Mystery",
            "Parody",
            "Poetry",
            "Romance",
            "Sci - Fi",
            "Spiritual",
            "Supernatural",
            "Suspense",
            "Tragedy",
            "Western",
        ]

        if val:
            if key in keys:
                try:
                    return key, int(val.replace(",", ""))
                except ValueError:
                    return key, val
            return None

        val = key

        lang = pycountry.languages.get(name=val)
        if lang:
            return "Language", lang.name

        tmp = split(val, "/")
        for x in tmp:
            if x in genres:
                return "Genres", tmp

        def parse_characters(chars: str) -> Characters:
            out_couples = []
            out_singles: List[str] = []
            couples = re.compile(r"\[([^\[]+)]")
            character_couples = couples.findall(chars)

            if character_couples:
                for couple in character_couples:
                    out_couples.append(split(couple))
                    chars = chars.replace(couple, "")
            if chars:
                chars = re.sub(r"[\[\]]", "", chars)
                out_singles = [s for s in split(chars) if s and s != " "]
            return {"couples": out_couples, "singles": out_singles}

        characters = ", ".join(split(val))

        return "Characters", parse_characters(characters)

    if not isinstance(input_data, list):
        raise TypeError(f"'{type(input_data)}' cannot be used here")

    data = [split(x, ":") for x in input_data]

    result_dictionary = {
        key: val
        for key, val in [parse_data(x) for x in data if parse_data(x)]
    }

    return result_dictionary


@attr.s(auto_attribs=True)
class FanFictionNetStory(Story):
    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        soup = BeautifulSoup(response.content, "html5lib").select_one("div#storytext")
        return clean_text(soup.contents)

    @property
    def select(self) -> str:
        return "span select#chap_select option"

    @staticmethod
    def chapter_parser(value: Tag) -> str:
        return re.sub(r"\d+\.\s+", "", value.text)

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""

        def check_date(timestamp: int) -> pendulum.DateTime:
            return pendulum.from_timestamp(timestamp, "UTC") if timestamp else None

        header = self.page.find(id="profile_top")
        _author = header.find("a", href=re.compile(r"^/u/\d+/"))
        tags = [
            x.string.strip() if x.name != "span" else x["data-xutime"]
            for x in header.find(class_="xgray").children
        ]
        _data = turn_into_dictionary(split(" ".join(tags), "-"))

        self.metadata.title = header.find("b").string
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.summary = header.find("div", class_="xcontrast_txt").string
        self.metadata.rating = _data.get("Rated")
        self.metadata.category = self.page.find(id="pre_story_links").find("a").string
        self.metadata.genres.items = _data.get("Genres")
        characters = _data.get("Characters")
        self.metadata.characters.singles = characters.get("singles") if characters else None
        self.metadata.characters.couples = characters.get("couples") if characters else None
        self.metadata.words = _data.get("Words")
        self.metadata.published = check_date(_data.get("Published"))
        self.metadata.updated = check_date(_data.get("Updated"))
        self.metadata.language = _data.get("Language")
        self.metadata.complete = _data.get("Status")

    def make_new_chapter_url(self, url: furl, value: str) -> furl:
        url.path.segments[-2] = value
        return url

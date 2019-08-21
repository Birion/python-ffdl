import re
from typing import Dict, List, Union

import attr
import iso639
import pendulum
from bs4 import BeautifulSoup, Tag
from furl import furl
from pendulum import DateTime
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class FanFictionNetStory(Story):
    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        soup = BeautifulSoup(page.content, "html5lib").select_one("div#storytext")
        return clean_text(soup.contents)

    @property
    def select(self) -> str:
        return "span select#chap_select option"

    @staticmethod
    def chapter_parser(value: Tag) -> str:
        return re.sub(r"\d+\.\s+", "", value.text)

    def turn_into_dictionary(self, input_data: List[str]) -> dict:
        """
        Transform a list with fic data into a dictionary.
        """
        if not isinstance(input_data, list):
            raise TypeError(f"'{type(input_data)}' cannot be used here")
        result_dictionary = {}
        for data in input_data:
            if ":" in data:
                temp_values = [x.strip() for x in data.split(": ")]
                key = temp_values[0]
                if re.match(r"^\d+(,\d+)*$", temp_values[1]):
                    temp_values[1] = re.sub(",", "", temp_values[1])
                    val = int(temp_values[1])
                else:
                    val = temp_values[1]
            else:
                if data == "OC":
                    key = "Characters"
                    val = data
                elif data == "Complete":
                    key = "Status"
                    val = data
                else:
                    lang = iso639.find(language=data)
                    if lang:
                        key = "Language"
                        val = lang["name"]
                    else:
                        key = "Characters"
                        val = [x.strip() for x in data.split(",")]
                        for x in data.split("/"):
                            genrefile = self.data / "genres"
                            with genrefile.open() as fp:
                                genres = [
                                    x.strip() for x in fp.readlines() if x != "\n"
                                ]
                            if x in genres:
                                key = "Genres"
                                val = data.split("/")
                                break
            result_dictionary[key] = val

        return result_dictionary

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def check_date(data: Dict[str, Union[str, int]], key: str) -> DateTime:
            timestamp = data.get(key)
            # noinspection PyTypeChecker
            return pendulum.from_timestamp(timestamp, "UTC") if timestamp else None

        def parse_characters(characters: str) -> Dict[str, List[str]]:
            out_couples = []
            out_singles = []
            couples = re.compile(r"\[[^[]+\]")
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

        header = self.page.find(id="profile_top")
        _author = header.find("a", href=re.compile(r"^/u/\d+/"))
        tags = [
            x.string.strip() if x.name != "span" else x["data-xutime"]
            for x in header.find(class_="xgray").children
        ]
        _data = self.turn_into_dictionary(
            re.sub(r"\s+", " ", " ".join(tags)).split(" - ")
        )

        if "Characters" in _data.keys():
            if isinstance(_data["Characters"], str):
                _data["Characters"] = [_data["Characters"]]
            _data["Characters"] = parse_characters(", ".join(_data["Characters"]))

        self.metadata.title = header.find("b").string
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = _author.string
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.summary = header.find("div", class_="xcontrast_txt").string
        self.metadata.rating = _data.get("Rated")
        self.metadata.category = self.page.find(id="pre_story_links").find("a").string
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

#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

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
from pyffdl.utilities import in_dictionary, turn_into_dictionary
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

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-2] = value
        return url

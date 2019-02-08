import sys
from datetime import date
from re import sub

import attr
import pendulum
from bs4 import BeautifulSoup, Tag
from click import echo, style
from ebooklib.epub import EpubHtml
from furl import furl
from requests import Response, get

from pyffdl.sites.story import Story


@attr.s(auto_attribs=True)
class AdultFanFictionStory(Story):
    _chapter_select: str = attr.ib(
        init=False, default="table:nth-of-type(3) .dropdown-content a"
    )

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

        page = BeautifulSoup(sub(r"<p></p>", "</p><p>", page.text), "html5lib")

        table = page("table")[2]
        contents = table("tr")[5].td

        if contents("p"):
            return "".join(map(str, contents("p")))
        else:
            contents = sub(r"<td>", "<p>", str(contents))
            contents = sub(r"</td>", "</p>", contents)
            contents = sub(r"<br/?>", "</p><p>", contents)
            contents = sub(r"<p></p>", "", contents)
            return contents

    @staticmethod
    def chapter_parser(value: Tag) -> str:
        return value.string.split("-")[-1]

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def check_date(timestr: str) -> date:
            if not timestr:
                return pendulum.from_timestamp(0, "local")
            return pendulum.from_format(timestr, "MMMM D, YYYY", "local")

        def get_data(url: str, title: str, page: int = 1) -> list:
            while True:
                if page > 20:
                    sys.exit(10)
                _url = furl(url)
                _url.args["page"] = page
                r = get(_url)
                q = BeautifulSoup(r.text, "html5lib")
                data = q.find(string=title)
                if not data:
                    page += 1
                else:
                    return data.find_parent("tbody")("td")

        _header = self._main_page("table")[2].table("td")
        _author = _header[1].a
        _title = _header[0].string
        _category = _header[1]("a")[-1]["href"]
        _data = get_data(_category, _title)
        _headings = _data[1].get_text(strip=True).split("-:-")
        _published = _data[0].get_text(strip=True).split(" : ")[-1]
        _updated = _headings[0].split(" : ")[-1].strip()
        _tags = _data[3].get_text(strip=True).split(":")[-1].split()

        self._story_metadata._title = _title
        self._story_metadata._author.name = _author.string
        self._story_metadata._author.url = _author["href"]
        self._story_metadata._summary = _data[2].get_text(strip=True)
        self._story_metadata._rating = _headings[1].strip().split(" : ")[-1]
        self._story_metadata._category = " ".join(
            [y.strip() for y in [x.string for x in _header[1].br.next_siblings][1:-2]]
        )
        # self.genres = in_dictionary(_data, "Genres")
        # self.characters = in_dictionary(_data, "Characters")
        # self.words = in_dictionary(_data, "Words")
        self._story_metadata._language = "English"
        self._story_metadata._published = check_date(_published)
        self._story_metadata._updated = check_date(_updated)
        self._story_metadata._complete = "COMPLETE" in _tags or "Oneshot" in _tags
        self._story_metadata._tags = _tags

        clean_title = sub(
            rf"{self.ILLEGAL_CHARACTERS}", "_", self._story_metadata._title
        )
        self._filename = (
            f"[ADULT] {self._story_metadata._author.name} - {clean_title}.epub"
        )

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.args["chapter"] = value
        return url

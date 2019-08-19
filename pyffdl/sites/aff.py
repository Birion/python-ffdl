import sys
from datetime import date
from re import sub

import attr
import pendulum
from bs4 import BeautifulSoup, Tag
from furl import furl
from requests import Response, get

from pyffdl.sites.story import Story


@attr.s(auto_attribs=True)
class AdultFanFictionStory(Story):
    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

        page = BeautifulSoup(sub(r"<p></p>", "</p><p>", page.text), "html5lib")

        table = page("table")[2]
        contents = table("tr")[5].td

        if contents("p"):
            return "".join(str(x) for x in contents("p"))
        replacement_strings = [("td>", "p>"), (r"<br/?>", "</p><p>"), ("<p></p>", "")]
        for r, s in replacement_strings:
            contents = sub(r, s, str(contents))
        return contents

    @staticmethod
    def chapter_parser(value: Tag) -> str:
        return value.string.split("-")[-1]

    @property
    def is_adult(self) -> bool:
        return True

    @property
    def select(self) -> str:
        return "table:nth-of-type(3) .dropdown-content a"

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        # noinspection PyTypeChecker
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

        _header = self.main_page("table")[2].table("td")
        _author = _header[1].a
        _title = _header[0].string
        _category = _header[1]("a")[-1]["href"]
        _data = get_data(_category, _title)
        _headings = _data[1].get_text(strip=True).split("-:-")
        _published = _data[0].get_text(strip=True).split(" : ")[-1]
        _updated = _headings[0].split(" : ")[-1].strip()
        _tags = _data[3].get_text(strip=True).split(":")[-1].split()

        self.metadata.title = _title
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = _author.string
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = _author["href"]
        self.metadata.summary = _data[2].get_text(strip=True)
        self.metadata.rating = _headings[1].strip().split(" : ")[-1]
        self.metadata.category = " ".join(
            [y.strip() for y in [x.string for x in _header[1].br.next_siblings][1:-2]]
        )
        self.metadata.language = "English"
        self.metadata.published = check_date(_published)
        self.metadata.updated = check_date(_updated)
        self.metadata.complete = "COMPLETE" in _tags or "Oneshot" in _tags
        self.metadata.tags = _tags

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.args["chapter"] = value
        return url

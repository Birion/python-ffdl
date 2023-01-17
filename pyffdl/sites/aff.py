import sys
from datetime import date
from re import sub

import attr
import pendulum  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from bs4.element import Tag  # type: ignore
from furl import furl  # type: ignore
from requests import Response, get

from pyffdl.sites.story import Story


@attr.s(auto_attribs=True)
class AdultFanFictionStory(Story):
    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        page = BeautifulSoup(sub(r"<p></p>", "</p><p>", response.text), "html5lib")

        contents = page.select_one("div#contentdata > ul > li:nth-of-type(7)")

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
        return ".dropdown-content > li > a"

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""  # noqa: D202

        # noinspection PyTypeChecker
        def check_date(timestr: str) -> date:
            if not timestr:
                return pendulum.from_timestamp(0, "local")
            try:
                return pendulum.from_format(timestr, "MMMM D, YYYY", "local")
            except ValueError:
                timestr = timestr.replace("am", "AM")
                timestr = timestr.replace("pm", "PM")
                return pendulum.from_format(timestr, "MMMM D, YYYY H:mm A", "local")

        def get_data(url: str, title: str, page: int = 1) -> list:
            while True:
                if page > 20:
                    sys.exit(10)
                _url = furl(url)
                _url.args["page"] = page
                r = get(_url.url)
                q = BeautifulSoup(r.text, "html5lib")
                data = q.find(string=title)
                if not data:
                    page += 1
                else:
                    return data.find_parent("tbody")("td")

        _header = self.page.select_one("table")("td")
        _author = _header[1].a
        _title = _header[0].string
        _category = _header[1]("a")[-1]["href"]

        self.metadata.title = _title
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = _author.string
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = _author["href"]
        self.metadata.category = " ".join(
            [y.strip() for y in [x.string for x in _header[1].br.next_siblings][1:-2]]
        )
        self.metadata.language = "English"

    def make_new_chapter_url(self, url: furl, value: str) -> furl:
        url.args["chapter"] = value
        return url

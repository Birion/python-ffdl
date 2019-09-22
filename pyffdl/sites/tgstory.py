import re
from typing import List, Optional, Tuple, Union, Any, Dict

import attr
import pendulum  # type: ignore
from bs4 import BeautifulSoup, Tag  # type: ignore
from furl import furl  # type: ignore
from requests import Response

from pyffdl.sites.story import Story, Metadata, Extra
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class TGStorytimeStory(Story):
    def _init(self):
        if self.page.select_one(".bigblock .errormsg"):
            self.url.query.add({"ageconsent": "ok"})
            main_page_request = self.session.get(self.url)
            if not main_page_request.ok:
                sysexit(1)
            self._page = BeautifulSoup(main_page_request.content, "html5lib")

    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        soup = BeautifulSoup(response.content, "html5lib")
        return clean_text([x for x in soup.select_one("#story span")])

    @staticmethod
    def chapter_parser(value: Tag) -> Tuple[int, str]:
        return int(value["value"]), re.sub(r"^\d+\.\s+", "", value.text)

    @property
    def select(self) -> str:
        return "select.textbox[name=chapter] option"

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""  # noqa: D202

        def get_clean_text(header: Any, selector: str) -> str:
            try:
                return header.select_one(selector).string.strip()
            except AttributeError:
                return "\n".join(header.select_one(selector).stripped_strings)


        def process_content(header: Any) -> Dict[str, Union[str, int]]:
            _ = " ".join(
                str(x).strip()
                for x in header.select_one(".content").contents
                if str(x).strip() != "" and x.name != "br"
            )

            _ = re.sub(r" ?</span>", "", _)

            _ = [x.strip() for x in re.split(r'<span class="label">', _) if x]

            data = {}

            for content in _:
                name, value = content.split(": ")
                value = ", ".join(
                    x
                    for x in BeautifulSoup(value, "html5lib").stripped_strings
                    if x != ","
                )
                if value.isdigit():
                    value = int(value)
                data[name] = value

            return data

        _header = self.page.select_one(".boxtop")
        self.metadata.title = get_clean_text(_header, "#pagetitle>a:first-of-type")
        _author = _header.select_one("#pagetitle>a:last-of-type")
        _author_url = furl(_author["href"])
        self.metadata.author.name = _author.string.strip()
        self.metadata.author.url = self.url.copy().set(
            path=_author_url.path, query_params=_author_url.query.params
        )
        self.metadata.summary = get_clean_text(_header, ".summarytext")

        content = process_content(_header)

        del content["Read"]
        del content["Chapters"]

        try:
            self.metadata.complete = content.pop("Completed") == "Completed Story"
        except KeyError:
            self.metadata.complete = False
        try:
            self.metadata.updated = pendulum.from_format(
                content.pop("Updated"), "MM/DD/YY"
            )
        except KeyError:
            self.metadata.updated = None

        self.metadata.published = pendulum.from_format(
            content.pop("Published"), "MM/DD/YY"
        )
        self.metadata.category = content.pop("Categories")
        self.metadata.words = content.pop("Word count")

        for key, value in content.items():
            self.metadata.extras.append(Extra(name=key, value=value))

    def make_new_chapter_url(self, url: furl, value: str) -> furl:
        url.query.params["chapter"] = value
        return url

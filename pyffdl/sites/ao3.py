from re import compile, sub
from typing import List, Tuple, Union

import attr
import pendulum
from bs4 import BeautifulSoup, Tag
from furl import furl
from requests import Response

from pyffdl.sites.story import Story
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class ArchiveOfOurOwnStory(Story):
    chapter_select: str = attr.ib(init=False, default="select#selected_id option")

    def __attrs_post_init__(self):
        if "chapters" not in self.url.path.segments:
            self.url.path.segments += ["chapters", "1"]
        if self.url.path.segments[-1] == "chapters":
            self.url.path.segments += ["1"]

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        soup = BeautifulSoup(page.content, "html5lib")
        return clean_text(
            [
                tag
                for contents in soup.select("div.userstuff")
                for tag in contents.children
                if isinstance(tag, Tag)
                and tag.name != "div"
                and tag.text != "Chapter Text"
                and (
                    "class" not in tag.attrs
                    or "class" in tag.attrs
                    and "title" not in tag["class"]
                )
            ]
        )

    @staticmethod
    def chapter_parser(value: Tag) -> Tuple[int, str]:
        return int(value["value"]), sub(r"^\d+\.\s+", "", value.text)

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def find_with_class(
            cls: str, elem: str = "dd", multi: bool = True
        ) -> Union[List[str], str, None]:
            try:
                _header = self.main_page.find("dl", class_="work meta group")
                _strings = [
                    x
                    for x in _header.find(elem, class_=cls).stripped_strings
                    if x != ""
                ]
                if multi:
                    return _strings
                return _strings[0] if _strings else None
            except AttributeError:
                return []

        _author = self.main_page.find("a", rel="author")
        _chapters = find_with_class("chapters", multi=False).split("/")
        self.metadata.complete = False
        if _chapters[-1].isdigit():
            if int(_chapters[0]) == len(self.metadata.chapters):
                self.metadata.complete = True

        self.metadata.title = self.main_page.find(
            "h2", class_="title heading"
        ).string.strip()
        self.metadata.author.name = _author.string
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.rating = find_with_class("rating", multi=False)
        self.metadata.updated = find_with_class("status", multi=False)
        self.metadata.published = pendulum.parse(
            find_with_class("published", multi=False)
        )
        if self.metadata.updated:
            self.metadata.updated = pendulum.parse(self.metadata.updated)
        if self.metadata.updated == self.metadata.published:
            self.metadata.updated = None
        self.metadata.language = find_with_class("language", multi=False)
        self.metadata.words = int(find_with_class("words", multi=False))
        self.metadata.summary = None
        self.metadata.genres = None
        self.metadata.category = ", ".join(find_with_class("fandom"))
        self.metadata.tags = find_with_class("freeform")

        characters = find_with_class("character")
        try:
            couples = [x.split("/") for x in find_with_class("relationship")]
        except AttributeError:
            couples = []
        _not_singles = {character for couple in couples for character in couple}

        self.metadata.characters = {
            "couples": couples,
            "singles": [
                character for character in characters if character not in _not_singles
            ],
        }

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        url.path.segments[-1] = value
        return url

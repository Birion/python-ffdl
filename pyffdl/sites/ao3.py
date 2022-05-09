import re
from typing import List, Optional, Tuple

import attr
import pendulum  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from bs4.element import Tag  # type: ignore
from furl import furl  # type: ignore
from requests import Response

from pyffdl.sites.story import Characters, Story
from pyffdl.utilities.misc import clean_text


@attr.s(auto_attribs=True)
class ArchiveOfOurOwnStory(Story):
    def _init(self):
        self.url.add({"view_adult": True})
        main_page_request = self.session.get(self.url.url)
        self.page = BeautifulSoup(main_page_request.content, "html5lib")
        self.url.path.segments = [x for x in self.url.path.segments if x != ""]
        if "chapters" not in self.url.path.segments:
            self.url.path.segments += ["chapters", "1"]
        if self.url.path.segments[-1] == "chapters":
            self.url.path.segments += ["1"]

    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""
        soup = BeautifulSoup(response.content, "html5lib")
        return clean_text(
            tag
            for tag in soup.select_one("div.userstuff").select("p, h1, h2, h3, h4, h5, h6, hr")
            if isinstance(tag, Tag) and tag.text != "Chapter Text" and (
                    "class" not in tag.attrs
                    or "class" in tag.attrs
                    and "title" not in tag["class"]
            )
        )

    @staticmethod
    def chapter_parser(value: Tag) -> Tuple[int, str]:
        return int(value["value"]), re.sub(r"^\d+\.\s+", "", value.text)

    @property
    def select(self) -> str:
        return "select#selected_id option"

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""  # noqa: D202

        def get_strings(cls: str) -> List[str]:
            result = _header.find("dd", class_=cls)
            if not result:
                return []
            return [x for x in result.stripped_strings if x != ""]

        def find_class_multiple(cls: str) -> List[str]:
            return get_strings(cls)

        def find_class_single(cls: str) -> Optional[str]:
            _strings = get_strings(cls)
            return _strings[0] if _strings else None

        def check_time(cls: str) -> Optional[pendulum.DateTime]:
            timestamp = find_class_single(cls) if _header else None
            if timestamp:
                return pendulum.parse(timestamp)
            return None

        _header = self.page.find("dl", class_="work meta group")

        _author = self.page.find("a", rel="author")
        _chapters = (
            find_class_single("chapters").split("/")  # type: ignore
            if _header and find_class_single("chapters")
            else []
        )
        self.metadata.complete = False
        if _chapters[-1].isdigit():
            if int(_chapters[0]) == len(self.metadata.chapters):
                self.metadata.complete = True

        self.metadata.title = self.page.find(
            "h2", class_="title heading"
        ).string.strip()
        # pylint:disable=assigning-non-slot
        self.metadata.author.name = _author.string
        # pylint:disable=assigning-non-slot
        self.metadata.author.url = self.url.copy().set(path=_author["href"])
        self.metadata.rating = find_class_single("rating") if _header else None
        self.metadata.updated = check_time("status")
        self.metadata.published = check_time("published")
        if self.metadata.updated == self.metadata.published:
            self.metadata.updated = None
        self.metadata.language = find_class_single("language") if _header else None
        self.metadata.words = (
            int(find_class_single("words"))  # type: ignore
            if _header and find_class_single("words")
            else 0
        )
        self.metadata.category = (
            ", ".join(find_class_multiple("fandom")) if _header else None
        )
        self.metadata.tags.items = find_class_multiple("freeform") if _header else []

        characters = find_class_multiple("character") if _header else []
        if characters:
            couples = [x.split("/") for x in find_class_multiple("relationship")]
        else:
            couples = []
        _not_singles = {character for couple in couples for character in couple}

        self.metadata.characters = Characters(
            couples=couples,
            singles=[
                character for character in characters if character not in _not_singles
            ]
        )

    def make_new_chapter_url(self, url: furl, value: str) -> furl:
        url.path.segments[-1] = value
        return url

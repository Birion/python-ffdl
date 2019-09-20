import re
from datetime import date
from io import BytesIO
from pathlib import Path
from sys import exit as sysexit
from typing import Any, ClassVar, Iterator, List, Optional, Tuple, Union
from uuid import uuid4

import attr
import iso639  # type: ignore
import pendulum  # type: ignore
from bs4 import BeautifulSoup  # type: ignore
from bs4.element import Tag  # type: ignore
from click import echo, style
from ebooklib import epub  # type: ignore
from ebooklib.epub import (  # type: ignore
    EpubBook,
    EpubHtml,
    EpubItem,
    EpubNav,
    EpubNcx,
    write_epub,
)
from furl import furl  # type: ignore
from jinja2 import Environment, select_autoescape
from requests import Response, Session

from pyffdl.utilities.covers import Cover
from pyffdl.utilities.misc import ensure_data, strlen


@attr.s
class Author:
    name: str = attr.ib(factory=str)
    url: furl = attr.ib(factory=furl, converter=furl)  # type: ignore


@attr.s(auto_attribs=True)
class Extra:
    name: str
    value: Union[int, str]


@attr.s
class Metadata:
    url: furl = attr.ib(factory=furl, converter=furl)  # type: ignore

    def __attrs_post_init__(self):  # noqa: D105
        self._title: str = ""
        self._author: Author = Author("", furl(""))
        self._complete: bool = False
        self._published: date = pendulum.local(1970, 1, 1)
        self._updated: date = pendulum.local(1970, 1, 1)
        self._downloaded: date = pendulum.now()
        self._language: str = "English"
        self._category: str = ""
        self._genres: List[str] = []
        self._characters: List[str] = []
        self._words: int = 0
        self._summary: str = ""
        self._rating: str = ""
        self._tags: List[str] = []
        self._chapters: List[str] = []
        self._extras: List[Extra] = []

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def complete(self):
        return self._complete

    @complete.setter
    def complete(self, value):
        self._complete = value

    @property
    def published(self):
        return self._published.to_iso8601_string() if self._published else None

    @published.setter
    def published(self, value):
        self._published = value

    @property
    def updated(self):
        return self._updated.to_iso8601_string() if self._updated else None

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def downloaded(self):
        return self._downloaded.to_iso8601_string() if self._downloaded else None

    @downloaded.setter
    def downloaded(self, value):
        self._downloaded = value

    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, value):
        self._language = value

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

    @property
    def genres(self):
        return "/".join(self._genres) if self._genres else None

    @genres.setter
    def genres(self, value):
        self._genres = value

    @property
    def characters(self):
        characters = ""
        if self._characters and self._characters.get("couples"):
            couples = [
                "[" + ", ".join(x) + "]" for x in self._characters.get("couples")
            ]
            characters += " ".join(couples)
            if self._characters.get("singles"):
                characters += " "
        if self._characters and self._characters.get("singles"):
            characters += ", ".join(self._characters.get("singles"))

        return characters if characters else None

    @characters.setter
    def characters(self, value):
        self._characters = value

    @property
    def words(self):
        return self._words

    @words.setter
    def words(self, value):
        self._words = value

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, value):
        self._summary = value

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        self._rating = value

    @property
    def tags(self):
        return ", ".join(self._tags) if self._tags else None

    @tags.setter
    def tags(self, value):
        self._tags = value

    @property
    def chapters(self):
        return self._chapters

    @chapters.setter
    def chapters(self, value):
        self._chapters = value

    @property
    def chapter_status(self):
        number_of_chapters = len(self._chapters) if self._complete else "??"
        return f"{len(self._chapters)}/{number_of_chapters}"

    @property
    def extras(self):
        return self._extras

    @extras.setter
    def extras(self, value):
        self._extras = value


@attr.s
class Datum:
    name: str = attr.ib()
    value: Any = attr.ib()
    url: bool = attr.ib(default=False)

    @property  # noqa: unused-variable
    def id(self):
        return f"{self.name.lower()}-url" if self.url else self.name.lower()


@attr.s
class FrontPage:
    title: str = attr.ib()
    author: str = attr.ib()
    data: List[Datum] = attr.ib()
    summary: str = attr.ib()

    TEMPLATE = """
        {% macro is_url(data, url) %}
            {% if url %}
                <a href="{{ data }}">{{ data }}</a>
            {% else %}
                {{ data }}
            {% endif %}
        {% endmacro %}
        {% macro print_data(datum) %}
            {% if datum.value %}
                <div id="{{ datum.id }}"><strong>{{ datum.name }}:</strong> {{ is_url(datum.value, datum.url) }}</div>
            {% endif %}
        {% endmacro %}
        <div class="header">
            <h1>{{ title }}</h1> by <h2>{{ author }}</h2>
        </div>
        <div class="titlepage">
            {% for datum in data %}
                {{ print_data(datum) }}
            {% endfor %}
            {% if summary %}
                <div>
                    <strong>Summary:</strong>
                    <p>{{ summary }}</p>
                </div>
            {% endif %}
        </div>
    """

    @classmethod
    def from_metadata(cls, metadata: Metadata):
        story_data = [
            Datum(name="Story", value=metadata.title),
            Datum(name="Author", value=metadata.author.name),
            Datum(name="URL", value=metadata.url, url=True),
            Datum(name="Author URL", value=metadata.author.url, url=True),
            Datum(name="Language", value=metadata.language),
            Datum(name="Rating", value=metadata.rating),
            Datum(name="Category", value=metadata.category),
            Datum(name="Genres", value=metadata.genres),
            Datum(name="Characters", value=metadata.characters),
            Datum(name="Published", value=metadata.published),
            Datum(name="Updated", value=metadata.updated),
            Datum(name="Downloaded", value=metadata.downloaded),
            Datum(name="Words", value=metadata.words),
            Datum(name="Tags", value=metadata.tags),
            Datum(name="Chapters", value=metadata.chapter_status),
        ]

        for extra in metadata.extras:
            story_data.append(Datum(name=extra.name, value=extra.value))

        return cls(metadata.title, metadata.author.name, story_data, metadata.summary)

    def __attrs_post_init__(self):  # noqa: D105
        self._env = Environment(autoescape=select_autoescape())

    @property
    def template(self):
        return self._env.from_string(self.TEMPLATE)

    def render(self):
        return self.template.render(
            title=self.title, author=self.author, data=self.data, summary=self.summary
        )


@attr.s()
class Story:
    url: furl = attr.ib(
        validator=attr.validators.instance_of(furl), converter=furl  # type: ignore
    )

    ILLEGAL_CHARACTERS: ClassVar = r'[<>:"/\|?]'

    def __attrs_post_init__(self):  # noqa: D105
        def prepare_style(file: Path) -> EpubItem:
            with file.open() as fp:
                return EpubItem(
                    uid=file.stem,
                    file_name=f"style/{file.name}",
                    media_type="text/css",
                    content=fp.read(),
                )

        self._filename = ""
        self._verbose = True
        self._force = False
        self._metadata = Metadata(self.url)
        self._session = Session()
        self._book = EpubBook()
        self._data_folder = ensure_data()
        self._styles = [
            prepare_style(file) for file in (self.data / "styles").glob("*.css")
        ]
        self._cover = None

        main_page_request = self.session.get(self.url)
        if not main_page_request.ok:
            sysexit(1)
        self._page = BeautifulSoup(main_page_request.content, "html5lib")

        self._init()

    def _init(self):
        pass

    def run(self):
        self.log(f"Downloading {self.url}", force=True)

        try:
            self.book = epub.read_epub(self.filename) if not self.force else None
        except (AttributeError, FileNotFoundError):
            pass

        self.make_title_page()

        try:
            cover = self.book.get_item_with_id("cover-img")
            self.cover = cover.content
        except (FileNotFoundError, AttributeError):
            with BytesIO() as b:
                cover = Cover.create(
                    self.metadata.title, self.metadata.author.name, self.data
                )
                cover.run()
                cover.image.save(b, format="jpeg")
                self.cover = b.getvalue()

        self.get_filename()
        self.get_chapters()
        self.make_ebook()

    @property
    def styles(self) -> List[EpubItem]:
        return self._styles

    @property
    def select(self) -> str:
        return ""

    @property
    def is_adult(self) -> bool:
        return False

    @property
    def is_verbose(self) -> bool:
        return self._verbose

    @is_verbose.setter
    def is_verbose(self, value):
        self._verbose = value

    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value):
        self._filename = value

    @property
    def metadata(self):
        return self._metadata

    @property
    def force(self):
        return self._force

    @force.setter
    def force(self, value):
        self._force = value

    @property
    def session(self):
        return self._session

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = value

    @property
    def book(self):
        return self._book

    @book.setter
    def book(self, value):
        self._book = value

    @property
    def cover(self):
        return self._cover

    @cover.setter
    def cover(self, value):
        self._cover = value

    @property
    def data(self):
        return self._data_folder

    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""

    @staticmethod
    def chapter_parser(value: Tag) -> Union[str, Tuple[int, str]]:
        """Processes the chapter titles to be stored in a usable format."""

    def log(self, text: str, force: bool = False):
        if self.is_verbose:
            echo(text)
        if force:
            if not self.is_verbose:
                echo(text)
            with open("pyffdl.log", "a") as fp:
                echo(text, file=fp)

    def get_chapters(self) -> None:
        """Gets the number of chapters and the base template for chapter URLs."""
        list_of_chapters = self.page.select(self.select)

        if list_of_chapters:
            self.metadata.chapters = [self.chapter_parser(x) for x in list_of_chapters]
        else:
            self.metadata.chapters = [self.metadata.title]

    def get_filename(self) -> None:
        clean_title = re.sub(rf"{self.ILLEGAL_CHARACTERS}", "_", self.metadata.title)
        pre = "[ADULT] " if self.is_adult else ""
        self.filename = (
            self.filename
            if self.filename
            else f"{pre}{self.metadata.author.name} - {clean_title}.epub"
        )

    def make_title_page(self) -> None:
        """Parses the main page for information about the story and author."""

    def make_new_chapter_url(self, url: furl, value: str) -> Optional[furl]:
        """Update base url with next chapter format."""

    @staticmethod
    def chapter_cleanup(chapters: List[Any]) -> List[str]:
        return chapters

    def step_through_chapters(self, chapters: list) -> Iterator[EpubHtml]:
        """Runs through the list of chapters and downloads each one."""  # noqa: D202

        def get_text(chapter_title: str) -> str:
            try:
                url_segment, chapter_title = chapter_title
            except (ValueError, TypeError):
                url_segment = str(index)
            # pylint:disable=assignment-from-no-return
            url = self.make_new_chapter_url(self.url.copy(), str(url_segment))
            if not url:
                return ""
            header = f"<h1>{chapter_title}</h1>"
            raw_chapter = self.session.get(url)
            full_text = header + self.get_raw_text(raw_chapter)
            self.log(
                f"Downloading chapter {style(chapter_number, bold=True, fg='blue')} - {style(chapter_title, fg='yellow')}"
            )
            return full_text

        chap_padding = (
            strlen(self.metadata.chapters) if strlen(self.metadata.chapters) > 2 else 2
        )

        self.metadata.chapters = self.chapter_cleanup(self.metadata.chapters)

        for _index, title in enumerate(self.metadata.chapters):
            index = _index + 1
            chapter_number = str(index).zfill(chap_padding)
            if index <= len(chapters):
                html = chapters[_index]
                text = str(BeautifulSoup(html.get_body_content(), "html5lib"))
            else:
                text = get_text(title)

            if isinstance(title, tuple):
                title = title[-1]
            chapter = EpubHtml(
                title=title,
                file_name=f"chapter{chapter_number}.xhtml",
                content=text,
                uid=f"chapter{chapter_number}",
            )
            for s in self.styles:
                chapter.add_item(s)
            yield chapter

    def make_ebook(self) -> None:
        """Combines everything to make an ePub book."""
        book = EpubBook()
        book.set_identifier(str(uuid4()))
        book.set_title(self.metadata.title)
        book.set_language(iso639.to_iso639_1(self.metadata.language))
        book.add_author(self.metadata.author.name)

        nav = EpubNav()
        ncx = EpubNcx()

        book.add_item(ncx)
        book.add_item(nav)

        current_chapters = (
            [
                x
                for x in self.book.get_items_of_type(9)
                if x.is_chapter() and x.file_name.startswith("chapter")
            ]
            if self.book
            else []
        )

        book.toc = [x for x in self.step_through_chapters(current_chapters)]

        book.set_cover("cover.jpg", self.cover)

        template = FrontPage.from_metadata(self.metadata)

        title_page = EpubHtml(
            title=self.metadata.title,
            file_name="title.xhtml",
            uid="title",
            content=template.render(),
        )

        for s in self.styles:
            title_page.add_item(s)
            book.add_item(s)
        book.add_item(title_page)

        book.spine = ["cover", title_page]

        for c in book.toc:
            book.add_item(c)
            book.spine.append(c)

        book.spine.append(nav)

        self.write(book)

    def write(self, book) -> None:
        """Create the epub file."""
        echo("Writing into " + style(self.filename, bold=True, fg="green"))
        write_epub(self.filename, book, {"tidyhtml": True, "epub3_pages": False})

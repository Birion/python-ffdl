import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, ClassVar, Iterator, List, Optional, Tuple, Union
from uuid import uuid4

import attr
import click
import cloudscraper
import pycountry
import pendulum
from bs4 import BeautifulSoup
from bs4.element import Tag
from click import echo, style
from ebooklib import epub
from ebooklib.epub import (
    EpubBook,
    EpubHtml,
    EpubItem,
    EpubNav,
    EpubNcx,
    write_epub,
)
from furl import furl
from jinja2 import Environment, select_autoescape
from pendulum import DateTime
from requests import Response, Session

from pyffdl.utilities.covers import Cover
from pyffdl.utilities.misc import ensure_data, strlen


def prepare_style(file: Path) -> EpubItem:
    with file.open() as fp:
        return EpubItem(
            uid=file.stem,
            file_name=f"style/{file.name}",
            media_type="text/css",
            content=fp.read(),
        )


@attr.s
class Author:
    name: str = attr.ib(factory=str)
    url: furl = attr.ib(factory=furl, converter=furl)


@attr.s(auto_attribs=True)
class Extra:
    name: str
    value: Union[int, str]


class MyDateTime(DateTime):
    def __str__(self):
        return self.to_iso8601_string()


@attr.s
class Listing:
    sep: str = attr.ib()
    items: List[str] = attr.ib(default=attr.Factory(list))

    def __str__(self):
        return self.sep.join(self.items) if self.items else ""


@attr.s
class Characters:
    singles: List[str] = attr.ib(default=attr.Factory(list))
    couples: List[str] = attr.ib(default=attr.Factory(list))

    def __str__(self):
        c = self.singles or self.couples
        characters = ""
        if c and self.couples:
            couples = [
                "[" + ", ".join(x) + "]" for x in self.couples
            ]
            characters += " ".join(couples)
            if self.singles:
                characters += " "
        if c and self.singles:
            characters += ", ".join(self.singles)

        return characters if characters else ""


@attr.s
class Metadata:
    url: furl = attr.ib(factory=furl, converter=furl)

    title: str = attr.ib(default="")
    author: Author = attr.ib(default=Author("", furl("")))
    complete: bool = attr.ib(default=False)
    published: MyDateTime = attr.ib(default=pendulum.local(1970, 1, 1))
    updated: MyDateTime = attr.ib(default=pendulum.local(1970, 1, 1))
    downloaded: MyDateTime = attr.ib(default=pendulum.now())
    language: str = attr.ib(default="English")
    category: str = attr.ib(default="")
    genres: Listing = attr.ib(default=Listing(sep="/"))
    characters: Characters = attr.ib(default=Characters())
    words: int = attr.ib(default=0)
    summary: str = attr.ib(default="")
    rating: str = attr.ib(default="")
    tags: Listing = attr.ib(default=Listing(sep=", "))
    chapters: List[str] = attr.ib(default=attr.Factory(list))
    extras: List[Extra] = attr.ib(default=attr.Factory(list))

    @classmethod
    def empty(cls):
        return cls(furl())

    @property
    def chapter_status(self):
        number_of_chapters = len(self.chapters) if self.complete else "??"
        return f"{len(self.chapters)}/{number_of_chapters}"


@attr.s
class Datum:
    name: str = attr.ib()
    value: Any = attr.ib()
    url: bool = attr.ib(default=False)

    @property
    def id(self) -> str:
        return re.sub(
            r"url-url",
            "url",
            f"{self.name.lower()}-url" if self.url else self.name.lower()
        ).replace(" ", "-").strip()


@attr.s
class FrontPage:
    title: str = attr.ib()
    author: str = attr.ib()
    data: List[Datum] = attr.ib()
    summary: str = attr.ib()
    env: Environment = attr.ib(default=Environment(autoescape=select_autoescape()))

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

    @property
    def template(self):
        return self.env.from_string(self.TEMPLATE)

    def render(self):
        return self.template.render(
            title=self.title, author=self.author, data=self.data, summary=self.summary
        )


class SelfSession(cloudscraper.CloudScraper):

    @classmethod
    def new(cls):
        s = Session()
        session = cloudscraper.create_scraper(sess=s, browser="chrome", delay=10, debug=True)
        return session


@attr.s()
class Story:
    url: furl = attr.ib(
        validator=attr.validators.instance_of(furl), converter=furl
    )

    cover: bytes = attr.ib(default=b"")
    verbose: bool = attr.ib(default=True)
    force: bool = attr.ib(default=False)
    session: SelfSession = attr.ib(default=SelfSession())
    filename: str = attr.ib(default="")
    metadata: Metadata = attr.ib(default=Metadata.empty())
    book: EpubBook = attr.ib(default=EpubBook())
    styles: List[EpubItem] = attr.ib(default=[])
    page: BeautifulSoup = attr.ib(default=BeautifulSoup("", "lxml"))
    data: Path = attr.ib(default=Path())

    chapters: List[str] = attr.ib(default=attr.Factory(list))
    author: str = attr.ib(default="")
    title: str = attr.ib(default="")

    ILLEGAL_CHARACTERS: ClassVar = r'[<>:"/\|?]'

    def __attrs_post_init__(self):

        self.metadata = Metadata(self.url)
        self.data = ensure_data()
        self.styles = [
            prepare_style(file) for file in (self.data / "styles").glob("*.css")
        ]

        main_page_request = self.session.get(self.url.url)
        if not main_page_request.ok:
            click.echo(f"I couldn't establish connection to {self.url}.\n{main_page_request.status_code}")
            sys.exit(1)
        self.page = BeautifulSoup(main_page_request.content, "html5lib")

        self._init()

    @classmethod
    def parse(cls, url, verbose, force):
        return cls(url, verbose=verbose, force=force)

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
    def select(self) -> str:
        return ""

    @property
    def is_adult(self) -> bool:
        return False

    @staticmethod
    def get_raw_text(response: Response) -> str:
        """Returns only the text of the chapter."""

    @staticmethod
    def chapter_parser(value: Tag) -> Union[str, Tuple[int, str]]:
        """Processes the chapter titles to be stored in a usable format."""

    def log(self, text: str, force: bool = False):
        if self.verbose:
            echo(text)
        if force:
            if not self.verbose:
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
            raw_chapter = self.session.get(url.url)
            full_text = header + self.get_raw_text(raw_chapter)
            cn = style(chapter_number, bold=True, fg='blue')
            ct = style(chapter_title, fg='yellow')
            self.log(
                f"Downloading chapter {cn} - {ct}"
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
        book.set_language(pycountry.languages.get(name=self.metadata.language).alpha_2)
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

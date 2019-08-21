import re
from datetime import date
from io import BytesIO
from sys import exit as sysexit
from typing import Any, ClassVar, Iterator, List, Tuple, Union
from uuid import uuid4
from pathlib import Path

import attr
import iso639
import pendulum
from bs4 import BeautifulSoup
from bs4.element import Tag
from click import echo, style
from ebooklib import epub
from ebooklib.epub import EpubBook, EpubHtml, EpubItem, EpubNav, EpubNcx, write_epub
from furl import furl
from jinja2 import Environment, select_autoescape
from requests import Response, Session

from pyffdl.utilities.covers import Cover
from pyffdl.utilities.misc import ensure_data, strlen


@attr.s
class Author:
    name: str = attr.ib(factory=str)
    url: furl = attr.ib(factory=furl, converter=furl)


@attr.s
class Metadata:
    url: furl = attr.ib(validator=attr.validators.instance_of(furl))

    def __attrs_post_init__(self):
        self._title: str = ""
        self._author: Author = Author("", furl(""))
        self._complete: bool = False
        self._published: date = pendulum.local(1970, 1, 1)
        self._updated: date = pendulum.local(1970, 1, 1)
        self._downloaded: date = pendulum.now()
        self._language: str = ""
        self._category: str = ""
        self._genres: List[str] = []
        self._characters: List[str] = []
        self._words: int = 0
        self._summary: str = ""
        self._rating: str = ""
        self._tags: List[str] = []
        self._chapters: List[str] = []

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
        return self._published

    @published.setter
    def published(self, value):
        self._published = value

    @property
    def updated(self):
        return self._updated

    @updated.setter
    def updated(self, value):
        self._updated = value

    @property
    def downloaded(self):
        return self._downloaded

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
        return self._genres

    @genres.setter
    def genres(self, value):
        self._genres = value

    @property
    def characters(self):
        return self._characters

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
        return self._tags

    @tags.setter
    def tags(self, value):
        self._tags = value

    @property
    def chapters(self):
        return self._chapters

    @chapters.setter
    def chapters(self, value):
        self._chapters = value


@attr.s
class Datum:
    name: str = attr.ib()
    value: Any = attr.ib()
    url: bool = attr.ib(default=False)

    def __attrs_post_init__(self):
        self._id = f"{self.name.lower()}-url" if self.url else self.name.lower()

    @property
    def id(self):
        return self._id


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
        number_of_chapters = len(metadata.chapters) if metadata.complete else "??"
        characters = ""
        if metadata.characters.get("couples"):
            couples = [
                "[" + ", ".join(x) + "]" for x in metadata.characters.get("couples")
            ]
            characters += " ".join(couples)
            if metadata.characters.get("singles"):
                characters += " "
        if metadata.characters.get("singles"):
            characters += ", ".join(metadata.characters.get("singles"))

        story_data = [
            Datum("Story", metadata.title),
            Datum("Author", metadata.author.name),
            Datum("URL", metadata.url, True),
            Datum("Author URL", metadata.author.url, True),
            Datum("Language", metadata.language),
            Datum("Rating", metadata.rating),
            Datum("Category", metadata.category),
            Datum("Genre", "/".join(metadata.genres) if metadata.genres else None),
            Datum("Characters", characters if characters else None),
            Datum(
                "Published",
                metadata.published.to_iso8601_string() if metadata.published else None,
            ),
            Datum(
                "Updated",
                metadata.updated.to_iso8601_string() if metadata.updated else None,
            ),
            Datum("Downloaded", metadata.downloaded.to_iso8601_string()),
            Datum("Words", metadata.words),
            Datum("Tags", ", ".join(metadata.tags) if metadata.tags else None),
            Datum("Chapters", f"{len(metadata.chapters)}/{number_of_chapters}"),
        ]

        return cls(metadata.title, metadata.author.name, story_data, metadata.summary)

    def __attrs_post_init__(self):
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
    url: furl = attr.ib(validator=attr.validators.instance_of(furl), converter=furl)

    ILLEGAL_CHARACTERS: ClassVar = r'[<>:"/\|?]'

    def __attrs_post_init__(self):
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
        self._styles = [prepare_style(file) for file in (self.data / "styles").glob("*.css")]
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
            self._book = epub.read_epub(self.filename) if not self.force else None
        except (AttributeError, FileNotFoundError):
            pass

        self.make_title_page()

        try:
            cover = self.book.get_item_with_id("cover-img")
            self._cover = cover.content
        except (FileNotFoundError, AttributeError):
            with BytesIO() as b:
                cover = Cover.create(
                    self.metadata.title, self.metadata.author.name, self.data
                )
                cover.run()
                cover.image.save(b, format="jpeg")
                self._cover = b.getvalue()

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

    @property
    def data(self):
        return self._data_folder

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

    @staticmethod
    def chapter_parser(value: Tag) -> Union[str, Tuple[int, str]]:
        """
        Processes the chapter titles to be stored in a usable format
        """

    def log(self, text: str, force: bool = False):
        if self.is_verbose:
            echo(text)
        if force:
            if not self.is_verbose:
                echo(text)
            with open("pyffdl.log", "a") as fp:
                echo(text, file=fp)

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
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
        """
        Parses the main page for information about the story and author.
        """

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        """
        Update base url with next chapter format.
        """

    def step_through_chapters(self, chapters: list) -> Iterator[EpubHtml]:
        """
        Runs through the list of chapters and downloads each one.
        """

        chap_padding = (
            strlen(self.metadata.chapters) if strlen(self.metadata.chapters) > 2 else 2
        )

        for _index, title in enumerate(self.metadata.chapters):
            index = _index + 1
            chapter_number = str(index).zfill(chap_padding)
            if index <= len(chapters):
                html = chapters[_index]
                text = str(BeautifulSoup(html.get_body_content(), "html5lib"))
            else:
                try:
                    url_segment, title = title
                except (ValueError, TypeError):
                    url_segment = index
                # pylint:disable=assignment-from-no-return
                url = self.make_new_chapter_url(self.url.copy(), url_segment)
                header = f"<h1>{title}</h1>"
                raw_chapter = self.session.get(url)
                text = header + self.get_raw_text(raw_chapter)
                self.log(
                    f"Downloading chapter {style(chapter_number, bold=True, fg='blue')} - {style(title, fg='yellow')}"
                )
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
        """
        Combines everything to make an ePub book.
        """
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

        self._write(book)

    def _write(self, book) -> None:
        """
        Create the epub file.
        """
        echo("Writing into " + style(self.filename, bold=True, fg="green"))
        write_epub(self.filename, book, {"tidyhtml": True, "epub3_pages": False})

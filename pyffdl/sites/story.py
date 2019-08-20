import re
from datetime import date, datetime
from io import BytesIO
from sys import exit as sysexit
from typing import ClassVar, Iterator, List, Tuple, Union
from uuid import uuid4

import attr
import iso639
import pendulum
from bs4 import BeautifulSoup
from bs4.element import Tag
from click import echo, style
from ebooklib import epub
from ebooklib.epub import EpubBook, EpubHtml, EpubItem, EpubNav, EpubNcx, write_epub
from furl import furl
from mako.template import Template
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

    title: str = attr.ib(init=False, factory=str)
    author: Author = attr.ib(init=False, factory=Author)
    complete: bool = attr.ib(init=False, default=False)
    published: date = attr.ib(init=False, default=pendulum.local(1970, 1, 1))
    updated: date = attr.ib(init=False, default=pendulum.local(1970, 1, 1))
    downloaded: datetime = attr.ib(init=False, default=pendulum.now())
    language: str = attr.ib(init=False, factory=str)
    category: str = attr.ib(init=False, factory=str)
    genres: List[str] = attr.ib(init=False, factory=list)
    characters: List[str] = attr.ib(init=False, factory=list)
    words: int = attr.ib(init=False, default=0)
    summary: str = attr.ib(init=False, factory=str)
    rating: str = attr.ib(init=False, factory=str)
    tags: List[str] = attr.ib(init=False, factory=list)
    chapters: List[str] = attr.ib(init=False, factory=list)


@attr.s()
class Story:
    url: furl = attr.ib(validator=attr.validators.instance_of(furl), converter=furl)

    ILLEGAL_CHARACTERS: ClassVar = r'[<>:"/\|?]'

    def __attrs_post_init__(self):
        self._filename = ""
        self._verbose = True
        self._force = False
        self._styles = ["style.css"]
        self._metadata = Metadata(self.url)
        self._session = Session()
        self._book = EpubBook()
        self._data_folder = ensure_data()
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

    def prepare_style(self, filename: str) -> EpubItem:
        cssfile = self.data / filename
        with cssfile.open() as fp:
            return EpubItem(
                uid=cssfile.stem,
                file_name=f"style/{cssfile.name}",
                media_type="text/css",
                content=fp.read(),
            )

    @property
    def styles(self) -> List[EpubItem]:
        # pylint:disable=not-an-iterable
        return [self.prepare_style(file) for file in self._styles]

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

        template = Template(filename=str(self.data / "title.mako"))

        title_page = EpubHtml(
            title=self.metadata.title,
            file_name="title.xhtml",
            uid="title",
            content=template.render(story=self.metadata),
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

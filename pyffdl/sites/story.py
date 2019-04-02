import logging
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from re import sub
from sys import exit
from typing import Iterator, List, Tuple, Union, ClassVar
from uuid import uuid4

import attr
import pendulum
from bs4 import BeautifulSoup, Tag
from click import echo, style
from ebooklib import epub
from ebooklib.epub import EpubBook, EpubHtml, EpubItem, EpubNav, EpubNcx, write_epub
from furl import furl
from iso639 import to_iso639_1
from mako.template import Template
from requests import Response, Session, codes

from pyffdl.utilities.covers import Cover
from pyffdl.utilities.misc import strlen


@attr.s
class Author:
    name: str = attr.ib(factory=str)
    url: furl = attr.ib(factory=furl)


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

    @classmethod
    def from_url(cls, url: furl):
        return cls(url)


@attr.s(auto_attribs=True)
class Story:
    url: furl = attr.ib(validator=attr.validators.instance_of(furl), converter=furl)
    verbose: bool = attr.ib()

    metadata: Metadata = attr.ib(init=False, default=Metadata(furl("")))
    datasource: Path = attr.ib(
        init=False, default=(Path(__file__) / ".." / ".." / "data").resolve()
    )
    filename: str = attr.ib(init=False, default=None)
    session: Session = attr.ib(init=False, factory=Session)
    _styles: List[str] = attr.ib(init=False, default=["style.css"])
    main_page: BeautifulSoup = attr.ib(init=False)
    chapter_select: str = attr.ib(init=False)
    adult: bool = attr.ib(init=False, default=False)
    force: bool = attr.ib(init=False, default=False)
    book: EpubBook = attr.ib(init=False, default=None)

    ILLEGAL_CHARACTERS: ClassVar = r'[<>:"/\|?]'

    def _initialise(self):
        self.metadata = Metadata.from_url(self.url)
        main_page_request = self.session.get(self.url)
        if main_page_request.status_code != codes.ok:
            exit(1)
        self.main_page = BeautifulSoup(main_page_request.content, "html5lib")
        try:
            self.book = epub.read_epub(self.filename) if not self.force else None
        except AttributeError:
            pass

    def run(self):
        echo(f"Downloading {self.url}")
        self._initialise()
        self.make_title_page()
        self.get_filename()
        self.get_chapters()
        self.make_ebook()

    def prepare_style(self, filename: str) -> EpubItem:
        cssfile = self.datasource / filename
        with cssfile.open() as fp:
            return EpubItem(
                uid=cssfile.stem,
                file_name=f"style/{cssfile.name}",
                media_type="text/css",
                content=fp.read(),
            )

    @property
    def styles(self):
        return [self.prepare_style(file) for file in self._styles]

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        pass

    @staticmethod
    def chapter_parser(value: Tag) -> Union[str, Tuple[int, str]]:
        return sub(r"\d+\.\s+", "", value.text)

    def log(self, text: str, force: bool = False):
        if self.verbose:
            echo(text)
        if force:
            echo(text)
            with open("pyffdl.log", "a") as fp:
                echo(text, file=fp)

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page.select(self.chapter_select)

        if list_of_chapters:
            self.metadata.chapters = [self.chapter_parser(x) for x in list_of_chapters]
        else:
            self.metadata.chapters = [self.metadata.title]

    def get_filename(self) -> None:
        clean_title = sub(rf"{self.ILLEGAL_CHARACTERS}", "_", self.metadata.title)
        pre = "[ADULT] " if self.adult else ""
        self.filename = (
            self.filename
            if self.filename
            else f"{pre}{self.metadata.author.name} - {clean_title}.epub"
        )

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """
        pass

    def make_new_chapter_url(self, url: furl, value: int) -> furl:
        """
        Update base url with next chapter format.
        """
        pass

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
                except ValueError:
                    url_segment = index
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

    def get_cover(self) -> bytes:
        try:
            cover = self.book.get_item_with_id("cover-img")
            return cover.content
        except (FileNotFoundError, AttributeError):
            with BytesIO() as b:
                cover = Cover.create(
                    self.metadata.title, self.metadata.author.name, self.datasource
                )
                cover.run()
                cover.image.save(b, format="jpeg")
                return b.getvalue()

    def make_ebook(self) -> None:
        """
        Combines everything to make an ePub book.
        """
        book = EpubBook()
        book.set_identifier(str(uuid4()))
        book.set_title(self.metadata.title)
        book.set_language(to_iso639_1(self.metadata.language))
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

        cover = self.get_cover()
        book.set_cover("cover.jpg", cover)

        template = Template(filename=str(self.datasource / "title.mako"))

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

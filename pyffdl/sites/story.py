from datetime import date
from io import BytesIO
from pathlib import Path
from sys import exit
from tempfile import TemporaryFile
from typing import Iterator, List
from uuid import uuid4

import attr
import pendulum
from bs4 import BeautifulSoup
from click import echo, style
from ebooklib.epub import EpubBook, EpubHtml, EpubItem, EpubNav, EpubNcx, write_epub
from furl import furl
from iso639 import to_iso639_1
from mako.template import Template
from requests import Response, Session, codes

from pyffdl.utilities.misc import strlen
from pyffdl.utilities.covers import make_cover


@attr.s
class Author:
    name: str = attr.ib(factory=str)
    url: furl = attr.ib(factory=furl)


@attr.s
class Metadata:
    url: furl = attr.ib(factory=furl, converter=furl)
    title: str = attr.ib(factory=str)
    author: Author = attr.ib(factory=Author)
    complete: bool = attr.ib(default=False)
    published: date = attr.ib(default=pendulum.local(1970, 1, 1))
    updated: date = attr.ib(default=pendulum.local(1970, 1, 1))
    language: str = attr.ib(factory=str)
    category: str = attr.ib(factory=str)
    genres: List[str] = attr.ib(factory=list)
    characters: List[str] = attr.ib(factory=list)
    words: int = attr.ib(default=0)
    summary: str = attr.ib(factory=str)
    rating: str = attr.ib(factory=str)
    tags: List[str] = attr.ib(factory=list)
    chapters: List[str] = attr.ib(factory=list)


@attr.s
class Story:
    url: furl = attr.ib(validator=attr.validators.instance_of(furl), converter=furl)
    main_page: BeautifulSoup = attr.ib(factory=BeautifulSoup)
    session: Session = attr.ib(factory=Session)
    stylefiles: list = attr.ib(default=["style.css"])
    filename: str = attr.ib(factory=str)
    metadata: Metadata = attr.ib(default=Metadata)

    styles: list = attr.ib(factory=list)
    datasource: Path = attr.ib(factory=Path)

    ILLEGAL_CHARACTERS = '[<>:"/\|?]'

    def __attrs_post_init__(self) -> None:
        self.metadata = Metadata(self.url)
        self.datasource = Path(__file__) / ".." / ".." / "data"
        self.datasource = self.datasource.resolve()

        self.styles = [self.prepare_style(file) for file in self.stylefiles]

        main_page_request = self.session.get(self.url)
        if main_page_request.status_code != codes.ok:
            exit(1)
        self.main_page = BeautifulSoup(main_page_request.content, "html5lib")

    def run(self):
        self.get_chapters()
        self.make_title_page()
        self.make_ebook()

    def prepare_style(self, filename: str) -> EpubItem:
        cssfile = self.datasource / filename
        with cssfile.open() as fp:
            css = fp.read()
        return EpubItem(
            uid=cssfile.stem,
            file_name=f"style/{cssfile.name}",
            media_type="text/css",
            content=css,
        )

    @staticmethod
    def get_raw_text(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        pass

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        pass

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

    def step_through_chapters(self) -> Iterator[EpubHtml]:
        """
        Runs through the list of chapters and downloads each one.
        """

        chap_padding = (
            strlen(self.metadata.chapters) if strlen(self.metadata.chapters) > 2 else 2
        )

        for index, title in enumerate(self.metadata.chapters):
            try:
                url_segment, title = title
            except ValueError:
                url_segment = index + 1
            url = self.make_new_chapter_url(self.url.copy(), url_segment)
            header = f"<h1>{title}</h1>"
            raw_chapter = self.session.get(url)
            text = header + self.get_raw_text(raw_chapter)
            chapter_number = str(index + 1).zfill(chap_padding)
            echo(
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

    def write_bookfile(self, book) -> None:
        """
        Create the epub file.
        """
        echo("Writing into " + style(self.filename, bold=True, fg="green"))
        write_epub(self.filename, book, {"tidyhtml": True, "epub3_pages": False})

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

        book.add_item(EpubNcx())
        book.add_item(nav)

        book.toc = [x for x in self.step_through_chapters()]

        with BytesIO() as b:
            cover_image = make_cover(self.datasource, self.metadata.title, self.metadata.author.name)
            cover_image.save(b, format="jpeg")
            book.set_cover("cover.jpg", b.getvalue())

        template = Template(filename=str(self.datasource / "title.mako"))

        title_page = EpubHtml(
            title=self.metadata.title,
            file_name="title.xhtml",
            uid="title",
            content=template.render(story=self.metadata),
        )

        for s in self.styles:
            title_page.add_item(s)
        book.add_item(title_page)

        for s in self.styles:
            book.add_item(s)

        book.spine = ["cover", title_page]

        for c in book.toc:
            book.add_item(c)
            book.spine.append(c)

        book.spine.append(nav)

        self.write_bookfile(book)

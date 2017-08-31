from datetime import date
from re import sub
from typing import Dict, List
from uuid import uuid4
from sys import exit

from bs4 import BeautifulSoup
from click import echo, style
from ebooklib import epub
from ebooklib.epub import EpubHtml, EpubBook, EpubNcx, EpubNav
from furl import furl
from iso639 import to_iso639_1
from os.path import join, dirname

from mako.template import Template
from requests import Response, Session
from requests import codes


class Story(object):
    def __init__(self, url: str) -> None:
        super(Story, self).__init__()

        self.main_url: furl = furl(url)
        self.main_page: BeautifulSoup = None
        self.session = Session()

        self.title: str = None
        self.author: Dict[str, str] = {
            "name": None,
            "url": None
        }

        self.chapters: List[EpubHtml] = []
        self.chapter_titles: List[str] = []

        self.complete: bool = False
        self.published: date = None
        self.updated: date = None

        self.language: str = None
        self.category: str = None
        self.genres: List[str] = []
        self.characters: List[str] = []
        self.words: int = None
        self.summary: str = None
        self.rating: str = None

    def run(self):

        self.setup()
        self.make_title_page()
        self.get_chapters()
        self.make_ebook()

    def setup(self) -> None:
        main_page_request = self.session.get(self.main_url)
        if main_page_request.status_code != codes.ok:
            exit(1)
        self.main_page = BeautifulSoup(main_page_request.content, "html5lib")

    @staticmethod
    def get_story(page: Response) -> str:
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

    def make_ebook(self) -> None:
        """
        Combines everything to make an ePub book.
        """
        book = EpubBook()
        book.set_identifier(str(uuid4()))
        book.set_title(self.title)
        book.set_language(to_iso639_1(self.language))
        book.add_author(self.author["name"])

        book.add_item(EpubNcx())
        book.add_item(EpubNav())

        with open(join(dirname(__file__), "style.css")) as fp:
            css = epub.EpubItem(
                uid="style",
                file_name="style/style.css",
                media_type="text/css",
                content=fp.read()
            )

        def digit_length(number: int) -> int:
            return len(str(number))

        chap_padding = digit_length(len(self.chapter_titles)) if digit_length(len(self.chapter_titles)) > 2 else 2

        for index, chapter in enumerate(self.chapter_titles):
            chapter_url = self.main_url.copy()
            chapter_url.path.segments[-2] = str(index + 1)
            header = f"<h1>{chapter}</h1>"
            raw_chapter = self.session.get(chapter_url)
            story = header + self.get_story(raw_chapter)
            chapter_number = str(index + 1).zfill(chap_padding)
            echo(
                "Downloading chapter "
                + style(chapter_number, bold=True, fg="blue")
                + " - "
                + style(chapter, fg="yellow")
            )
            _chapter = epub.EpubHtml(
                title=chapter,
                file_name=f"chapter{chapter_number}.xhtml",
                content=story,
                uid=f"chapter{chapter_number}"
            )
            _chapter.add_item(css)
            self.chapters.append(_chapter)

        book.toc = [x for x in self.chapters]

        template = Template(filename=join(dirname(__file__), "title.mako"))

        title_page = epub.EpubHtml(
            title=self.title,
            file_name="title.xhtml",
            uid="title",
            content=template.render(
                story=self
            )
        )
        title_page.add_item(css)
        book.add_item(title_page)

        book.add_item(css)

        book.spine = [title_page]

        for c in self.chapters:
            book.add_item(c)
            book.spine.append(c)

        book.spine.append("nav")

        bookname = f"{self.author['name']} - {sub(r'[:/]', '_', self.title)}.epub"

        echo("Writing into " + style(bookname, bold=True, fg="green"))

        epub.write_epub(bookname, book, {"tidyhtml": True})

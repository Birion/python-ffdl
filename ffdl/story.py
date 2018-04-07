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
    ILLEGAL_CHARACTERS = '[<>:"/\|?]'
    def __init__(self, url: str) -> None:
        super(Story, self).__init__()

        self.main_url: furl = furl(url)
        self.main_page: BeautifulSoup = None
        self.session = Session()

        self.styles = []

        self.filename: str = None

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
        self.tags: List[str] = []

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

    def step_through_chapters(self) -> None:
        """
        Runs through the list of chapters and downloads each one.
        """
        pass

    def write_bookfile(self, book) -> None:
        """
        Create the epub file.
        """
        echo("Writing into " + style(self.filename, bold=True, fg="green"))
        epub.write_epub(self.filename, book, {"tidyhtml": True})

    def make_ebook(self, extra_css: str=None) -> None:
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

        if not extra_css:
            style_file = join(dirname(__file__), "style.css")
        else:
            style_file = extra_css

        with open(style_file) as fp:
            _css = epub.EpubItem(
                uid="style",
                file_name="style/style.css",
                media_type="text/css",
                content=fp.read()
            )
            self.styles.append(_css)

        self.step_through_chapters()

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
        for s in self.styles:
            title_page.add_item(s)
        book.add_item(title_page)

        for s in self.styles:
            book.add_item(s)

        book.spine = [title_page]

        for c in self.chapters:
            book.add_item(c)
            book.spine.append(c)

        book.spine.append("nav")

        self.write_bookfile(book)


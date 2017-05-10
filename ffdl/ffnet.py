from os.path import join, dirname
from re import sub, compile
from sys import exit
from uuid import uuid4
from datetime import date
from typing import List, Dict

from click import echo, style
from iso639 import to_iso639_1
from requests import get, Response
from bs4 import BeautifulSoup
from ebooklib import epub
from furl import furl
from mako.template import Template

from ffdl.misc import dictionarise, in_dictionary


class Story(object):
    def __init__(self, url: str) -> None:
        super(Story, self).__init__()
        self.main_url: furl = furl(url)
        self.main_page: BeautifulSoup = None

        self.title: str = None
        self.author: Dict[str, str] = {
            "name": None,
            "url": None
        }

        self.chapters: List[epub.EpubHtml] = []
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

        self.setup()
        self.make_title_page()
        self.get_chapters()

    def setup(self) -> None:
        main_page_request = get(self.main_url)
        if main_page_request.status_code != 200:
            exit(1)
        self.main_page = BeautifulSoup(main_page_request.content, "html5lib")

    @staticmethod
    def get_story(page: Response) -> str:
        """
        Returns only the text of the chapter
        """
        return "".join([
            str(x) for x in
            BeautifulSoup(page.content, "html5lib").find("div", class_="storytext").contents
        ])

    def get_chapters(self):
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page.find("select", id="chap_select")

        if list_of_chapters:
            self.chapter_titles = [sub(r"\d+\. ", "", x.string) for x in list_of_chapters("option")]
        else:
            self.chapter_titles = [self.title]

    def make_title_page(self):
        """
        Parses the main page for information about the story and author.
        """
        _header = self.main_page.find(id="profile_top")
        _author = _header.find("a", href=compile(r"^/u/\d+/"))
        _data = dictionarise([x.strip() for x in " ".join(_header.find(class_="xgray").stripped_strings).split(" - ")])

        echo(_data)

        published = in_dictionary(_data, "Published")
        updated = in_dictionary(_data, "Updated")

        def check_date(in_date: str) -> date:
            if not in_date:
                return date(1970, 1, 1)
            if "m" in in_date or "h" in in_date:
                return date.today()
            story_date = [int(x) for x in in_date.split("/")]
            if len(story_date) == 2:
                story_date.append(date.today().year)
            return date(story_date[2], story_date[0], story_date[1])

        self.title = _header.find("b").string
        self.author["name"] = _author.string
        self.author["url"] = self.main_url.copy().set(path=_author["href"])
        self.summary = _header.find("div", class_="xcontrast_txt").string
        self.rating = in_dictionary(_data, "Rated")
        self.category = self.main_page.find(id="pre_story_links").find("a").string
        self.genres = in_dictionary(_data, "Genres")
        self.characters = in_dictionary(_data, "Characters")
        self.words = in_dictionary(_data, "Words")
        self.published = check_date(published)
        self.updated = check_date(updated)
        self.language = in_dictionary(_data, "Language")
        self.complete = in_dictionary(_data, "Status")

    def make_ebook(self):
        """
        Combines everything to make an ePub book.
        """
        book = epub.EpubBook()
        book.set_identifier(str(uuid4()))
        book.set_title(self.title)
        book.set_language(to_iso639_1(self.language))
        book.add_author(self.author)

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
            story = header + self.get_story(get(chapter_url))
            chapter_number = str(index + 1).zfill(chap_padding)
            echo(
                "Downloading chapter "
                + style(chapter_number, bold=True, fg="blue")
                + " - "
                + style(chapter, fg="yellow")
            )
            _chapter = epub.EpubHtml(
                title=chapter,
                file_name=f"chapter_{chapter_number}.xhtml",
                content=story
            )
            _chapter.add_item(css)
            self.chapters.append(_chapter)

        book.toc = (x for x in self.chapters)

        book.add_item(epub.EpubNcx())

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

        bookname = f"{self.author} - {sub(r'[:/]', '_', self.title)}.epub"

        echo("Writing into " + style(bookname, bold=True, fg="green"))

        epub.write_epub(
            bookname, book, {}
        )

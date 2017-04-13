# coding=utf-8

import os.path
import re
import sys
import uuid
from datetime import date

import click
import iso639
import requests as r
from bs4 import BeautifulSoup
from ebooklib import epub
from furl import furl
from mako.template import Template
from typing import List

GENRES = [
    "Adventure",
    "Angst",
    "Crime",
    "Drama",
    "Family",
    "Fantasy",
    "Friendship",
    "General",
    "Horror",
    "Humor",
    "Hurt/Comfort",
    "Mystery",
    "Parody",
    "Poetry",
    "Romance",
    "Sci-Fi",
    "Spiritual",
    "Supernatural",
    "Suspense",
    "Tragedy",
    "Western"
]
LANGUAGES = [x["name"] for x in iso639.data]


def dictionarise(data: List[str]) -> dict:
    """
    Transform a list with fic data into a dictionary.
    """
    dic = {}
    key, val = None, None
    for index, i in enumerate(data):
        if ":" in i:
            _ = [x.strip() for x in i.split(":")]
            key = _[0]
            val = _[1] if not _[1].isdigit() else int(_[1])
        else:
            if i in LANGUAGES:
                key = "Language"
                val = i
            else:
                key = "Characters"
                val = [x.strip() for x in i.split(",")]
                for x in i.split("/"):
                    if x in GENRES:
                        key = "Genres"
                        val = i.split("/")
                        break
        dic[key] = val

    return dic


def in_dictionary(dic: dict, key: str) -> str:
    return dic[key] if key in dic.keys() else None


class Story(object):
    def __init__(self, url: str) -> None:
        super(Story, self).__init__()
        self.main_url: furl = furl(url)
        self.main_page: BeautifulSoup = None

        self.title: str = None
        self.author: str = None
        self.author_url: str = None

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
        main_page_request = r.get(self.main_url)
        if main_page_request.status_code != 200:
            sys.exit(1)
        self.main_page = BeautifulSoup(main_page_request.content, "html5lib")

    @staticmethod
    def get_story(page: r.models.Response) -> str:
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
            self.chapter_titles = [re.sub(r"\d+\. ", "", x.string) for x in list_of_chapters("option")]
        else:
            self.chapter_titles = [self.title]

    def make_title_page(self):
        """
        Parses the main page for information about the story and author.
        """
        _header = self.main_page.find(id="profile_top")
        _author = _header.find("a", href=re.compile(r"^/u/\d+/"))
        _data = dictionarise([x.strip() for x in " ".join(_header.find(class_="xgray").stripped_strings).split(" - ")])

        click.echo(_data)

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
        self.author = _author.string
        self.author_url = self.main_url.copy().set(path=_author["href"])
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
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(self.title)
        book.set_language(iso639.to_iso639_1(self.language))
        book.add_author(self.author)

        with open(os.path.join(os.path.dirname(__file__), "style.css")) as fp:
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
            story = header + self.get_story(r.get(chapter_url))
            chapter_number = str(index + 1).zfill(chap_padding)
            click.echo(
                "Downloading chapter "
                + click.style(chapter_number, bold=True, fg="blue")
                + " - "
                + click.style(chapter, fg="yellow")
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

        template = Template(filename=os.path.join(os.path.dirname(__file__), "title.mako"))

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

        bookname = f"{self.author} - {re.sub(r'[:/]', '_', self.title)}.epub"

        click.echo("Writing into " + click.style(bookname, bold=True, fg="green"))

        epub.write_epub(
            bookname, book, {}
        )

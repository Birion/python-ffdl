# coding=utf-8

import os.path
import re
import sys
import uuid
from datetime import date
from typing import List
from urllib.parse import urlparse

import click
import iso639
import requests as r
from bs4 import BeautifulSoup
from ebooklib import epub
from mako.template import Template


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
            val = _[1]
        else:
            if index == 1:
                key = "Language"
                val = i
            if index == 2:
                key = "Genre"
                val = i
        dic[key] = val

    return dic


def in_dictionary(dic: dict, key: str) -> str:
    return dic[key] if key in dic.keys() else None


class Story(object):
    def __init__(self, url: str) -> None:
        super(Story, self).__init__()
        self.title = str
        self.author = str
        self.author_url = str
        self.language = str
        self.chapters = []  # type: List[epub.EpubHtml]
        self.chapter_titles = []  # type: List[str]
        self.main_url = url
        self.chapter_url = str
        self.complete = False
        self.published = date
        self.updated = date
        self.category = str
        self.genre = str
        self.words = int
        self.summary = str
        self.rating = str

        self.main_page_request = r.get(self.main_url)
        if self.main_page_request.status_code != 200:
            sys.exit(1)
        self.main_page = BeautifulSoup(self.main_page_request.content, "html5lib")

        self.make_title_page()
        self.get_chapters()

    def combine_url(self, partial: str) -> str:
        """
        Returns a URL combining the base URL and the partial URL provided as parameter.
        """
        base_url = urlparse(self.main_url)
        return base_url.scheme + "://" + base_url.netloc + partial

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
            chap_url = self.combine_url(list_of_chapters["onchange"][16:-1].strip("'"))

            self.chapter_titles = [re.sub(r"\d+\. ", "", x.string) for x in list_of_chapters("option")]
            self.chapter_url = re.sub(r"'\+ this.options\[this.selectedIndex\].value \+ '", "{}", chap_url)
        else:
            self.chapter_titles = [self.title]
            self.chapter_url = self.main_url

    def make_title_page(self):
        """
        Parses the main page for information about the story and author.
        """
        _header = self.main_page.find(id="profile_top")
        _author = _header.find("a", href=re.compile(r"^/u/\d+/"))
        _data = dictionarise(
            [x.strip() for x in " ".join([x for x in _header.find(class_="xgray").stripped_strings]).split(" - ")])

        click.echo(_data)

        published = in_dictionary(_data, "Published")
        updated = in_dictionary(_data, "Updated")

        pub_day = 1
        pub_month = 1
        pub_year = 1970
        up_day = 1
        up_month = 1
        up_year = 1970

        if published:
            if "m" in published or "h" in published:
                pub_month, pub_day, pub_year = (date.today().month, date.today().day, date.today().year)
            else:
                pubd = [int(x) for x in published.split("/")]
                if len(pubd) == 2:
                    pubd.append(date.today().year)
                pub_month, pub_day, pub_year = pubd
        if updated:
            if "m" in updated or "h" in updated:
                up_month, up_day, up_year = (date.today().month, date.today().day, date.today().year)
            else:
                upd = [int(x) for x in updated.split("/")]
                if len(upd) == 2:
                    upd.append(date.today().year)
                up_month, up_day, up_year = upd

        words = in_dictionary(_data, "Words")

        self.title = _header.find("b").string
        self.author = _author.string
        self.author_url = self.combine_url(_author["href"])
        self.summary = _header.find("div", class_="xcontrast_txt").string
        self.rating = in_dictionary(_data, "Rated")
        self.category = self.main_page.find(id="pre_story_links").find("a").string
        self.genre = in_dictionary(_data, "Genre")
        self.words = int(words.replace(",", ""))
        self.published = date(pub_year, pub_month, pub_day)
        self.updated = date(up_year, up_month, up_day)
        self.language = iso639.to_iso639_1(in_dictionary(_data, "Language"))
        self.complete = in_dictionary(_data, "Status")

    def make_ebook(self):
        """
        Combines everything to make an ePub book.
        """
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(self.title)
        book.set_language(self.language)
        book.add_author(self.author)

        with open(os.path.join(os.path.dirname(__file__), "style.css")) as fp:
            css = epub.EpubItem(
                uid="style",
                file_name="style/style.css",
                media_type="text/css",
                content=fp.read()
            )

        chap_padding = len(str(len(self.chapters))) if len(str(len(self.chapters))) > 2 else 2

        for index, chapter in enumerate(self.chapter_titles):
            chapter_url = self.chapter_url.format(str(index + 1))
            header = "<h1>" + chapter + "</h1>"
            story = header + self.get_story(r.get(chapter_url))
            chapter_number = str(index + 1).zfill(chap_padding)
            click.echo("Downloading chapter " + click.style(chapter_number, bold=True) + " - " + chapter)
            _chapter = epub.EpubHtml(
                title=chapter,
                file_name="chapter_{}.xhtml".format(chapter_number),
                content=story
            )
            _chapter.add_item(css)
            self.chapters.append(_chapter)

        book.toc = (x for x in self.chapters)

        book.add_item(epub.EpubNcx())

        template = Template(filename=os.path.join(os.path.dirname(__file__), "nav.mako"))

        nav = epub.EpubHtml(
            title=self.title,
            file_name="nav.xhtml",
            uid="nav",
            content=template.render(
                story=self
            )
        )
        nav.add_item(css)

        book.add_item(nav)

        book.add_item(css)
        book.spine = [nav]

        for c in self.chapters:
            book.add_item(c)
            book.spine.append(c)

        bookname = '{author} - {title}.epub'.format(author=self.author, title=re.sub(r"[:/]", "_", self.title))

        click.echo("Writing into " + click.style(bookname, bold=True))

        epub.write_epub(
            bookname, book, {}
        )

#!/usr/bin/env python3
# coding=utf-8

import re
import sys
import uuid
from datetime import date
from urllib.parse import urlparse

import click
import iso639
import requests as r
from bs4 import BeautifulSoup
from ebooklib import epub
from mako.template import Template


class Story(object):
    def __init__(self, url):
        super(Story, self).__init__()
        self.title = str
        self.author = str
        self.author_url = str
        self.lang = str
        self.chapters = []
        self.chapter_titles = []
        self.main_url = url
        self.chapter_url = str
        self.complete = False
        self.published = date
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
    def get_story(page) -> str:
        """
        Returns only the text of the chapter
        """
        return "".join(
            [str(x) for x in BeautifulSoup(page.content, "html5lib").find("div", class_="storytext").contents])

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
        _data = [x for x in _header.find(class_="xgray").stripped_strings]
        _month, _day, _year = [int(x) for x in _data[-2].split("/")]
        _data2 = [x.strip() for x in _data[2].split("- ") if x]

        self.title = _header.find("b").string
        self.author = _author.string
        self.author_url = self.combine_url(_author["href"])
        self.summary = _header.find("div", class_="xcontrast_txt").string
        self.rating = _data[1].split()[-1]
        self.category = self.main_page.find(id="pre_story_links").find("a").string
        self.genre = _data2[1]
        self.words = int(_data2[-2].split()[-1].replace(",", ""))
        self.published = date(_year, _month, _day)
        self.lang = iso639.to_iso639_1(_data2[0])
        self.complete = "Complete" in _data[-1]

    def make_ebook(self):
        """
        Combines everything to make an ePub book.
        """
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title(self.title)
        book.set_language(self.lang)
        book.add_author(self.author)

        with open("style.css") as fp:
            css = epub.EpubItem(
                uid="style",
                file_name="style/style.css",
                media_type="text/css",
                content=fp.read()
            )

        for index, chapter in enumerate(self.chapter_titles):
            chapter_url = self.chapter_url.format(index + 1)
            header = "<h1>" + chapter + "</h1>"
            story = header + self.get_story(r.get(chapter_url))
            _chapter = epub.EpubHtml(
                title=chapter,
                file_name="chapter_{}.xhtml".format(str(index + 1).zfill(2)),
                content=story
            )
            _chapter.add_item(css)
            self.chapters.append(_chapter)

        book.toc = (x for x in self.chapters)

        book.add_item(epub.EpubNcx())
        # book.add_item(epub.EpubNav())

        template = Template(filename="nav.mako")

        nav = epub.EpubHtml(
            title=self.title,
            file_name="nav.xhtml",
            uid="nav",
            content=template.render(
                story=self
            )
        )
        book.add_item(nav)

        book.add_item(css)
        book.spine = [nav]

        for c in self.chapters:
            book.add_item(c)
            book.spine.append(c)

        epub.write_epub('{author} - {title}.epub'.format(author=self.author, title=self.title), book, {})


@click.command()
@click.argument("url")
def cli(url: str):
    story = Story(url)
    story.make_ebook()


if __name__ == '__main__':
    cli()

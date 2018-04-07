from datetime import date
from re import sub, compile
from typing import List, Dict
import sys
import arrow

from bs4 import BeautifulSoup
from click import echo, style
from requests import Response, get
from ebooklib import epub
from ebooklib.epub import EpubHtml, EpubBook, EpubNcx, EpubNav
from furl import furl

from ffdl.misc import dictionarise, in_dictionary
from ffdl.story import Story


class AdultFanFictionStory(Story):
    def __init__(self, url: str) -> None:
        super(AdultFanFictionStory, self).__init__(url)

    @staticmethod
    def get_story(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

        p = BeautifulSoup(sub(r"<p></p>", "</p><p>", page.text), "html5lib")

        t = p("table")[2]
        c = t("tr")[5].td

        if c("p"):
            return "".join(map(str, c("p")))
        else:
            d = sub(r"<td>", "<p>", str(c))
            d = sub(r"</td>", "</p>", d)
            d = sub(r"<br/?>", "</p><p>", d)
            d = sub(r"<p></p>", "", d)
            return d

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page("table")[2].find(class_="dropdown-content")("a")

        if list_of_chapters:
            self.chapter_titles = [x.string.split("-")[-1] for x in list_of_chapters]
        else:
            self.chapter_titles = [self.title]

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """
        def check_date(input_date: str) -> date:
            if not input_date:
                return date(1970, 1, 1)
            else:
                return arrow.get(input_date, "MMMM D, YYYY").date()

        def get_data(url: str, title: str,  page: int=1) -> list:
            while True:
                if page > 20:
                    sys.exit(10)
                _url = furl(url)
                _url.args["page"] = page
                r = get(_url)
                q = BeautifulSoup(r.text, "html5lib")
                data = q.find(string=title)
                if not data:
                    page += 1
                else:
                    return data.find_parent("tbody")("td")

        _header = self.main_page("table")[2].table("td")
        _author = _header[1].a
        _title = _header[0].string
        _category = _header[1]("a")[-1]["href"]
        _data = get_data(_category, _title)
        _headings = _data[1].get_text(strip=True).split("-:-")
        _published = _data[0].get_text(strip=True).split(" : ")[-1]
        _updated = _headings[0].split(" : ")[-1].strip()
        _tags = _data[3].get_text(strip=True).split(":")[-1].split()

        self.title = _title
        self.author["name"] = _author.string
        self.author["url"] = _author["href"]
        self.summary = _data[2].get_text(strip=True)
        self.rating = _headings[1].strip().split(" : ")[-1]
        self.category = " ".join([y.strip() for y in [x.string for x in _header[1].br.next_siblings][1:-2]])
        # self.genres = in_dictionary(_data, "Genres")
        # self.characters = in_dictionary(_data, "Characters")
        # self.words = in_dictionary(_data, "Words")
        self.language = "English"
        self.published = check_date(_published)
        self.updated = check_date(_updated)
        self.complete = "COMPLETE" in _tags or "Oneshot" in _tags
        self.tags = _tags

        clean_title = sub(rf'{self.ILLEGAL_CHARACTERS}', '_', self.title)
        self.filename = f"[ADULT] {self.author['name']} - {clean_title}.epub"

    def step_through_chapters(self) -> None:
        """
        Runs through the list of chapters and downloads each one.
        """
        def digit_length(number: int) -> int:
            return len(str(number))

        chap_padding = digit_length(len(self.chapter_titles)) if digit_length(len(self.chapter_titles)) > 2 else 2

        for index, chapter in enumerate(self.chapter_titles):
            chapter_url = self.main_url.copy()
            chapter_url.args["chapter"] = index + 1
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
            _chapter = EpubHtml(
                title=chapter,
                file_name=f"chapter{chapter_number}.xhtml",
                content=story,
                uid=f"chapter{chapter_number}"
            )
            for s in self.styles:
                _chapter.add_item(s)
            self.chapters.append(_chapter)


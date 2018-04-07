from datetime import date
from re import sub, compile
from typing import List, Dict

from bs4 import BeautifulSoup
from click import echo, style
from requests import Response
from ebooklib import epub
from ebooklib.epub import EpubHtml, EpubBook, EpubNcx, EpubNav

from ffdl.misc import dictionarise, in_dictionary
from ffdl.story import Story


class FanFictionNetStory(Story):
    def __init__(self, url: str) -> None:
        super(FanFictionNetStory, self).__init__(url)

    @staticmethod
    def get_story(page: Response) -> str:
        """
        Returns only the text of the chapter
        """

        return "".join([
            sub(r"\s+", " ", str(x).strip()) for x
            in BeautifulSoup(page.content, "html5lib").find("div", class_="storytext").contents
        ])

    def get_chapters(self) -> None:
        """
        Gets the number of chapters and the base template for chapter URLs
        """
        list_of_chapters = self.main_page.find("select", id="chap_select")

        if list_of_chapters:
            self.chapter_titles = [sub(r"\d+\. ", "", x.string) for x in list_of_chapters("option")]
        else:
            self.chapter_titles = [self.title]

    def make_title_page(self) -> None:
        """
        Parses the main page for information about the story and author.
        """

        def check_date(input_date: str) -> date:
            if not input_date:
                return date(1970, 1, 1)
            if "m" in input_date or "h" in input_date:
                return date.today()
            story_date = [int(x) for x in input_date.split("/")]
            if len(story_date) == 2:
                story_date.append(date.today().year)
            return date(story_date[2], story_date[0], story_date[1])

        def parse_characters(characters: str) -> Dict[str, List[str]]:
            out_couples = []
            out_singles = []
            couples = compile(r"\[[^[]+\]")
            character_couples = [x for x in couples.finditer(characters)]

            if character_couples:
                num_couples = len(character_couples)
                for couple in character_couples:
                    out_couples.append(couple.group()[1:-1].split(", "))
                for i in range(-1, -num_couples - 1, -1):
                    match = character_couples[i]
                    characters = characters.replace(match.group(), "").strip()
            if characters:
                out_singles = characters.split(", ")
            return {"couples": out_couples, "singles": out_singles}

        _header = self.main_page.find(id="profile_top")
        _author = _header.find("a", href=compile(r"^/u/\d+/"))
        _data = dictionarise([x.strip() for x in " ".join(_header.find(class_="xgray").stripped_strings).split(" - ")])

        if "Characters" in _data.keys():
            _data["Characters"] = ", ".join(_data["Characters"])
            echo(_data)
            _data["Characters"] = parse_characters(_data["Characters"])
        else:
            echo(_data)

        published = in_dictionary(_data, "Published")
        updated = in_dictionary(_data, "Updated")

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

        clean_title = sub(rf'{self.ILLEGAL_CHARACTERS}', '_', self.title)
        self.filename = f"{self.author['name']} - {clean_title}.epub"

    def step_through_chapters(self) -> None:
        """
        Runs through the list of chapters and downloads each one.
        """
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
            _chapter = EpubHtml(
                title=chapter,
                file_name=f"chapter{chapter_number}.xhtml",
                content=story,
                uid=f"chapter{chapter_number}"
            )
            for s in self.styles:
                _chapter.add_item(s)
            self.chapters.append(_chapter)


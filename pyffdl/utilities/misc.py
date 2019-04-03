from re import sub, compile
from typing import KeysView, List, Set, Tuple, Union
import logging

from bs4 import BeautifulSoup
from ebooklib import epub
import iso639
import click

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
    "Western",
]


def list2text(input_list: Union[KeysView[str], List[str]]) -> str:
    if len(input_list) == 1:
        return input_list[0]
    elif len(input_list) == 2:
        return " and ".join(input_list)
    else:
        input_list[-1] = "and " + input_list[-1]
        return ", ".join(input_list)


def turn_into_dictionary(input_data: List[str]) -> dict:
    """
    Transform a list with fic data into a dictionary.
    """
    if not isinstance(input_data, list):
        raise TypeError(f"'{type(input_data)}' cannot be used here")
    dic = {}
    key, val = None, None
    for index, i in enumerate(input_data):
        if ":" in i:
            _ = [x.strip() for x in i.split(": ")]
            key = _[0]
            val = _[1] if not _[1].isdigit() else int(_[1])
        else:
            if i == "OC":
                key = "Characters"
                val = i
            else:
                lang = iso639.find(i)
                if lang:
                    key = "Language"
                    val = lang["name"]
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


def get_url_from_file(file: Union[str, click.Path]) -> Union[str, None]:
    book = epub.read_epub(file)
    title_page = book.get_item_with_id("title")
    if not title_page:  # if we're checking old-format ebook
        title_page = book.get_item_with_id("nav")
    try:
        parsed_text = BeautifulSoup(title_page.content, "html5lib")
        url = parsed_text.find(id="story-url")
        if not url:
            url = parsed_text
        return url("a")[0]["href"]
    except AttributeError:
        error = f"File {file} doesn't contain requested information."
        with open("pyffdl.log", "a") as fp:
            click.echo(error, file=fp)
        click.echo(error, err=True)
        return None


def strlen(data: list) -> int:
    return len(str(len(data)))


def clean_text(text: Union[List, Tuple, Set]) -> str:
    if not (isinstance(text, list) or isinstance(text, tuple) or isinstance(text, set)):
        raise TypeError
    raw_text = " ".join(sub(r"\s+", " ", str(x).strip()) for x in text)
    raw_text = sub(r"\s*(<br/?>\s*){2,}\s*", "</p><p>", raw_text)
    if not raw_text.endswith("</p>"):
        raw_text = raw_text + "</p>"
    raw_text = sub(r"<p></p>", "", raw_text)
    raw_text = sub("</p><p>", "</p>\n<p>", raw_text)
    raw_text = sub(r"<hr", r"\n<hr", raw_text)
    raw_text = sub(r"\s([.!?])", r"\1", raw_text)
    if raw_text.startswith("<"):
        raw_text = sub(r"(</h\d>)\s*([^<])", r"\1<p>\2", raw_text)
    else:
        raw_text = "<p>" + raw_text
    raw_text = sub(r'<p/?>\s*<div class=.hr.>\s*<hr/?>\s*</div>\s*<br/?>\s*', "<hr/>\n<p>", raw_text)
    raw_text = sub(r"(</p>|</h\d>)", r"\1\n\n", raw_text)
    raw_text = sub(r"(<p>|<h\d>)", r"\n\n\1", raw_text)
    raw_text = sub(r"\n(\s*\n)+", r"\n\n", raw_text)
    raw_text = sub(r"^\s+", "", raw_text)
    raw_text = sub(r"\s+(</p>|</h\d>)", r"\1", raw_text)
    raw_text = sub(r"\.\.+", "&hellip;", raw_text)
    raw_text = sub(r"(<hr[^>]*>)\s*(.+)", r"\1\n\n<p>\2</p>", raw_text)

    parsed_text = BeautifulSoup(raw_text, "html5lib")
    for tag in parsed_text.find_all("p", string=compile(r"^(?P<a>.)(?P=a)+$")):
        tag["class"] = "center"
    for tag in parsed_text.find_all("hr"):
        tag["class"] = "center"
    return "".join(str(x) for x in parsed_text.body.contents)

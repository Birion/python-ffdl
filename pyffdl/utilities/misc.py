from re import sub, compile, match
from typing import KeysView, List, Set, Tuple, Union
import logging

import attr
from bs4 import BeautifulSoup
from ebooklib import epub
import iso639
import click

GENRES = [
    "Adventure",
    "Angst",
    "Comfort",
    "Crime",
    "Drama",
    "Family",
    "Fantasy",
    "Friendship",
    "General",
    "Horror",
    "Humor",
    "Hurt",
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
    result_dictionary = {}
    for index, data in enumerate(input_data):
        if ":" in data:
            temp_values = [x.strip() for x in data.split(": ")]
            key = temp_values[0]
            if match(r"^\d+(,\d+)*$", temp_values[1]):
                temp_values[1] = sub(",", "", temp_values[1])
                val = int(temp_values[1])
            else:
                val = temp_values[1]
        else:
            if data == "OC":
                key = "Characters"
                val = data
            elif data == "Complete":
                key = "Status"
                val = data
            else:
                lang = iso639.find(language=data)
                if lang:
                    key = "Language"
                    val = lang["name"]
                else:
                    key = "Characters"
                    val = [x.strip() for x in data.split(",")]
                    for x in data.split("/"):
                        if x in GENRES:
                            key = "Genres"
                            val = data.split("/")
                            break
        result_dictionary[key] = val

    return result_dictionary


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
    if not isinstance(text, (list, tuple, set)):
        raise TypeError
    raw_text = "<p>" + " ".join(sub(r"\s+", " ", str(x).strip()) for x in text) + "</p>"
    replacement_strings = [
        (r"(</h\d>)\s*([^<])", r"\1<p>\2"),
        (r"\s*(<br/?>\s*){2,}\s*", "</p><p>"),
        (r"</?p></p>", ""),
        ("</p><p>", "</p>\n<p>"),
        (r"<hr", r"\n<hr"),
        (r"\s(\.[^0-9]|[!?])", r"\1"),
        (r"<p/?>\s*<div class=.hr.>\s*<hr/?>\s*</div>\s*<br/?>\s*", "<hr/>\n<p>"),
        (r"(</p>|</h\d>)", r"\1\n\n"),
        (r"(<p>|<h\d>)", r"\n\n\1"),
        (r"\n(\s*\n)+", r"\n\n"),
        (r"^\s+", ""),
        (r"\s+(</p>|</h\d>)", r"\1"),
        (r"\.\.+", "&hellip;"),
        (r"(<hr[^>]*>)\s*(.+)", r"\1\n\n<p>\2</p>"),
    ]

    for r, s in replacement_strings:
        raw_text = sub(r, s, raw_text)

    parsed_text = BeautifulSoup(raw_text, "html5lib")
    for tag in parsed_text.find_all("p", string=compile(r"^(?P<a>.)(?P=a)+$")):
        tag["class"] = "center"
    for tag in parsed_text.find_all("hr"):
        tag["class"] = "center"
    return "".join(str(x) for x in parsed_text.body.contents)

import re
import shutil
from pathlib import Path
from typing import KeysView, List, Set, Tuple, Union

import click
from bs4 import BeautifulSoup
from ebooklib import epub

APP = "pyffdl"


def list2text(input_list: Union[KeysView[str], List[str]]) -> str:
    if len(input_list) == 1:
        return input_list[0]
    if len(input_list) == 2:
        return " and ".join(input_list)
    input_list[-1] = "and " + input_list[-1]
    return ", ".join(input_list)


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
    raw_text = (
        "<p>" + " ".join(re.sub(r"\s+", " ", str(x).strip()) for x in text) + "</p>"
    )
    replacement_strings = [
        (r"(</h\d>)\s*([^<])", r"\1<p>\2"),
        (r"\s*(<br/?>\s*){2,}\s*", "</p><p>"),
        (r"</?p></p>", ""),
        ("</p><p>", "</p>\n<p>"),
        (r"<hr", r"\n<hr"),
        (r"(<(strong|em|i|b)>.+) (</\2>)", r"\1\3 "),
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
        raw_text = re.sub(r, s, raw_text)

    parsed_text = BeautifulSoup(raw_text, "html5lib")
    for tag in parsed_text.find_all("p", string=re.compile(r"^(?P<a>.)(?P=a)+$")):
        tag["class"] = "center"
    for tag in parsed_text.find_all("hr"):
        tag["class"] = "center"
    return "".join(str(x) for x in parsed_text.body.contents)


def ensure_data() -> Path:
    data_folder = Path(click.get_app_dir(APP))
    src_folder = Path(__file__).resolve().parents[1] / "data"

    if not data_folder.exists():
        data_folder.mkdir()

    for section in src_folder.iterdir():
        target = data_folder / section.name
        if not target.exists():
            func = shutil.copy if section.is_file() else shutil.copytree
            func(section, target)

    return data_folder

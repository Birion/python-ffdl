from typing import List, Union

from bs4 import BeautifulSoup
from ebooklib import epub
from iso639 import data

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
LANGUAGES = [x["name"] for x in data]


def list2text(input_list: List[str]) -> str:
    if len(input_list) == 1:
        return input_list[0]
    elif len(input_list) == 2:
        return " and ".join(input_list)
    else:
        input_list[-1] = "and " + input_list[-1]
        return ", ".join(input_list)


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


def in_dictionary(dic: dict, key: Union[str, int, tuple]) -> str:
    return dic[key] if key in dic.keys() else None


def get_url_from_file(file: str) -> str:
    book = epub.read_epub(file)
    title_page = book.get_item_with_id("title")
    parsed_text = BeautifulSoup(title_page.content, "html5lib")
    url = parsed_text.find(id="story-url")
    if not url:
        url = parsed_text
    return url("a")[0]["href"]

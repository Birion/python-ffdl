import pytest
from pathlib import Path
from pyffdl.utilities.misc import *


def test_list2text():
    assert list2text(["foo"]) == "foo"
    assert list2text(["foo", "bar"]) == "foo and bar"
    assert list2text(["foo", "bar", "baz"]) == "foo, bar, and baz"


def test_turn_into_dictionary():
    with pytest.raises(TypeError):
        turn_into_dictionary(7)
    with pytest.raises(TypeError):
        turn_into_dictionary([7])
    with pytest.raises(TypeError):
        turn_into_dictionary("Chapter: 7")
    assert turn_into_dictionary(["English"]) == {"Language": "English"}
    assert turn_into_dictionary(["Updated: 12.2.2019"]) == {"Updated": "12.2.2019"}
    assert turn_into_dictionary(["Pages: 173"]) == {"Pages": 173}
    assert turn_into_dictionary(["Harry, [Hermione, Ron]"]) == {'Characters': ['Harry', '[Hermione', 'Ron]']}
    assert turn_into_dictionary(["Romance"]) == {'Genres': ['Romance']}


def test_in_dictionary():
    dic = {"foo": "bar", "baz": None, "1": 1, 1: "1"}
    assert in_dictionary(dic, "foo") == "bar"
    assert not in_dictionary(dic, "bar")
    assert in_dictionary(dic, "1") == 1
    assert in_dictionary(dic, 1) == "1"


@pytest.mark.parametrize(
    "filename,url",
    [
        ("good_file.epub", "http://www.fanfiction.net/s/7954090/1/"),
        ("bad_file.epub", None),
    ],
)
def test_get_url_from_file(filename, url):
    path = Path("./tests/data/")
    assert get_url_from_file(path / filename) == url


def test_strlen():
    assert strlen([]) == 1
    assert strlen(list(range(10))) == 2
    with pytest.raises(TypeError):
        strlen(10)


def test_clean_text():
    with pytest.raises(TypeError):
        clean_text("string")
    with pytest.raises(TypeError):
        clean_text(7)
    with pytest.raises(TypeError):
        clean_text(18.7)
    assert clean_text({x for x in range(10)}) == "0 1 2 3 4 5 6 7 8 9"
    assert clean_text([x for x in range(10)]) == "0 1 2 3 4 5 6 7 8 9"
    assert clean_text(["foo", "bar"]) == "foo bar"
    assert clean_text(["fo o", "ba          r"]) == "fo o ba r"
    assert clean_text((" foo      ", " bar")) == "foo bar"

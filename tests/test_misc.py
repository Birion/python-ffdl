import pytest
from pathlib import Path

from furl import furl

from pyffdl.utilities.misc import *
from pyffdl.sites.ffnet import FanFictionNetStory, turn_into_dictionary


def test_list2text():
    assert list2text(["foo"]) == "foo"
    assert list2text(["foo", "bar"]) == "foo and bar"
    assert list2text(["foo", "bar", "baz"]) == "foo, bar, and baz"


def test_turn_into_dictionary():
    story = FanFictionNetStory("https://www.fanfiction.net")
    with pytest.raises(TypeError):
        turn_into_dictionary(7)
    with pytest.raises(TypeError):
        turn_into_dictionary([7])
    with pytest.raises(TypeError):
        turn_into_dictionary("Chapter: 7")
    assert turn_into_dictionary(["English"]) == {"Language": "English"}
    assert turn_into_dictionary(["Updated: 12.2.2019"]) == {"Updated": "12.2.2019"}
    assert turn_into_dictionary(["Pages: 173"]) == {}
    assert turn_into_dictionary(["Harry, [Hermione, Ron]"]) == {
        "Characters": {"couples": [["Hermione", "Ron"]], "singles": ["Harry"]}
    }
    assert turn_into_dictionary(["Romance"]) == {"Genres": ["Romance"]}


@pytest.mark.parametrize(
    "filename,url",
    [
        ("good_file.epub", furl("http://www.fanfiction.net/s/7954090/1/")),
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
    assert clean_text({x for x in range(10)}) == "<p>0 1 2 3 4 5 6 7 8 9</p>\n\n"
    assert clean_text([x for x in range(10)]) == "<p>0 1 2 3 4 5 6 7 8 9</p>\n\n"
    assert clean_text(["foo", "bar"]) == "<p>foo bar</p>\n\n"
    assert clean_text(["fo o", "ba          r"]) == "<p>fo o ba r</p>\n\n"
    assert clean_text((" foo      ", " bar")) == "<p>foo bar</p>\n\n"


def test_ensure_data():
    assert ensure_data() == Path(click.get_app_dir("pyffdl"))


def test_split():
    assert split("foo,bar") == ["foo", "bar"]
    assert split("foobar") == ["foobar"]
    assert split("foo, bar") == ["foo", "bar"]
    assert split("foo, bar", sep="/") == ["foo, bar"]
    assert split("foo, bar/baz", sep="/") == ["foo, bar", "baz"]
    with pytest.raises(TypeError):
        split(0)
    with pytest.raises(TypeError):
        split(["foo, bar"])
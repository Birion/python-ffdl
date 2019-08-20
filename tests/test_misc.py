import pytest
from pathlib import Path
from pyffdl.utilities.misc import *
from pyffdl.sites.ffnet import FanFictionNetStory


def test_list2text():
    assert list2text(["foo"]) == "foo"
    assert list2text(["foo", "bar"]) == "foo and bar"
    assert list2text(["foo", "bar", "baz"]) == "foo, bar, and baz"


def test_turn_into_dictionary():
    story = FanFictionNetStory("https://www.fanfiction.net")
    with pytest.raises(TypeError):
        story.turn_into_dictionary(7)
    with pytest.raises(TypeError):
        story.turn_into_dictionary([7])
    with pytest.raises(TypeError):
        story.turn_into_dictionary("Chapter: 7")
    assert story.turn_into_dictionary(["English"]) == {"Language": "English"}
    assert story.turn_into_dictionary(["Updated: 12.2.2019"]) == {"Updated": "12.2.2019"}
    assert story.turn_into_dictionary(["Pages: 173"]) == {"Pages": 173}
    assert story.turn_into_dictionary(["Harry, [Hermione, Ron]"]) == {'Characters': ['Harry', '[Hermione', 'Ron]']}
    assert story.turn_into_dictionary(["Romance"]) == {'Genres': ['Romance']}


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
    assert clean_text({x for x in range(10)}) == "<p>0 1 2 3 4 5 6 7 8 9</p>\n\n"
    assert clean_text([x for x in range(10)]) == "<p>0 1 2 3 4 5 6 7 8 9</p>\n\n"
    assert clean_text(["foo", "bar"]) == "<p>foo bar</p>\n\n"
    assert clean_text(["fo o", "ba          r"]) == "<p>fo o ba r</p>\n\n"
    assert clean_text((" foo      ", " bar")) == "<p>foo bar</p>\n\n"

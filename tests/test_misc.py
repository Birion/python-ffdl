import pytest
from pyffdl.utilities.misc import *


def test_list2text():
    assert list2text(["foo"]) == "foo"
    assert list2text(["foo", "bar"]) == "foo and bar"
    assert list2text(["foo", "bar", "baz"]) == "foo, bar, and baz"


def test_in_dictionary():
    dic = {
        "foo": "bar",
        "baz": None,
        "1": 1,
        1: "1"
    }
    assert in_dictionary(dic, "foo") == "bar"
    assert not in_dictionary(dic, "bar")
    assert in_dictionary(dic, "1") == 1
    assert in_dictionary(dic, 1) == "1"


def test_strlen():
    assert strlen([]) == 1
    assert strlen(list(range(10))) == 2

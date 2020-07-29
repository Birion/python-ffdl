import pytest
import requests

from pyffdl.sites.story import *


@pytest.mark.parametrize(
    "exception,url",
    [
        (requests.exceptions.MissingSchema, None),
        (requests.exceptions.MissingSchema, "net"),
        (requests.exceptions.InvalidURL, "https://"),
        (requests.exceptions.InvalidSchema, "hppt://httpbin.org"),
        (SystemExit, "http://httpbin.org/status/404"),
    ],
)
def test_check_setup(exception, url):
    with pytest.raises(exception):
        story = Story(url)


def test_check_empty_setup():
    with pytest.raises(TypeError):
        story = Story()


def test_prepare_style():
    with pytest.raises(AttributeError):
        prepare_style("style.css")
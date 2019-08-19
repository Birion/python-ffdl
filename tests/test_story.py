import pytest
import requests
from bs4 import BeautifulSoup

from pyffdl.sites.story import Story


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
        story._initialise()


def test_check_empty_setup():
    with pytest.raises(TypeError):
        story = Story()

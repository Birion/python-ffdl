import pytest
import requests
from bs4 import BeautifulSoup

from ffdl.story import Story


@pytest.mark.parametrize("exception,url", [
    (requests.exceptions.MissingSchema, None),
    (requests.exceptions.MissingSchema, "net"),
    (requests.exceptions.InvalidURL, "https://"),
    (requests.exceptions.InvalidSchema, "hppt://httpbin.org")
])
def test_check_setup(exception, url):
    with pytest.raises(exception):
        story = Story(url)
        story.setup()


def test_check_empty_setup():
    with pytest.raises(TypeError):
        story = Story()


def test_check_setup_with_nonexistent_url():
    story = Story("http://httpbin.org/status/404")
    assert story.setup() == 1


def test_setup():
    story = Story("http://httpbin.org/html")
    story.setup()
    with open("html") as fp:
        html = BeautifulSoup(fp.read(), "html5lib")
    assert story.main_page == html

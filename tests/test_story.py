import pytest
import requests
from bs4 import BeautifulSoup

from pyffdl.sites.story import Story


@pytest.mark.parametrize("exception,url", [
    (requests.exceptions.MissingSchema, None),
    (requests.exceptions.MissingSchema, "net"),
    (requests.exceptions.InvalidURL, "https://"),
    (requests.exceptions.InvalidSchema, "hppt://httpbin.org")
])
def test_check_setup(exception, url):
    with pytest.raises(exception):
        story = Story(url)


def test_check_empty_setup():
    with pytest.raises(TypeError):
        story = Story()


def test_check_setup_with_nonexistent_url():
    with pytest.raises(SystemExit):
        story = Story("http://httpbin.org/status/404")

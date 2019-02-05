from typing import List, Tuple

import click
from furl import furl

from pyffdl.__version__ import __version__
from pyffdl.sites import (
    AdultFanFictionStory,
    ArchiveOfOurOwnStory,
    FanFictionNetStory,
    TwistingTheHellmouthStory,
    HTMLStory,
)
from pyffdl.utilities import get_url_from_file, list2text

AVAILABLE_SITES = {
    "fanfiction.net": FanFictionNetStory,
    "fictionpress.com": FanFictionNetStory,
    "adult-fanfiction.org": AdultFanFictionStory,
    "archiveofourown.org": ArchiveOfOurOwnStory,
    "tthfanfic.org": TwistingTheHellmouthStory,
}


def download(urls: List[str]) -> None:
    for address in urls:
        host = ".".join(furl(address).host.split(".")[-2:])
        if host in AVAILABLE_SITES.keys():
            story = AVAILABLE_SITES[host](address)
            story.run()
        else:
            click.echo(
                f"{__file__} is currently only able to download from {list2text(AVAILABLE_SITES.keys())}."
            )


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command("download", help="Download a new fanfiction story.")
@click.option("-f", "--from", "from_file", type=click.File(), help="Load a list of URLs from a plaintext file.")
@click.argument("url_list", nargs=-1)
def cli_download(from_file: click.File, url_list: Tuple[str, ...]) -> None:
    urls = [x for x in url_list]
    if from_file:
        urls += [x.strip("\n") for x in from_file.readlines()]
    download(urls)


@cli.command("simple", help="Download a single story, using a list of chapter URLs.")
@click.option("-f", "--from", "from_file", type=click.File(), help="Load a list of URLs from a plaintext file.")
@click.option("-a", "--author", help="Name of the author", type=str, required=True)
@click.option("-t", "--title", help="Title of the story", type=str, required=True)
@click.argument("url_list", nargs=-1)
def cli_simple(from_file: click.File, author: str, title: str, url_list: Tuple[str, ...]):
    urls = [x for x in url_list]
    if from_file:
        urls += [x.strip("\n") for x in from_file.readlines()]
    if not urls:
        click.echo("You must provide at least one URL to download.")
        return
    story = HTMLStory(
        chapters=urls,
        author=author,
        title=title,
        url=furl("http://httpbin.org/status/200"),
    )
    story.run()


@cli.command("update", help="Update an existing .epub fanfiction file.")
@click.argument("filename", type=click.Path(dir_okay=False, exists=True))
def cli_update(filename: click.Path) -> None:
    download([get_url_from_file(filename)])

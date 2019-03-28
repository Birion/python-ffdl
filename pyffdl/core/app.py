import shutil
from typing import List, Tuple, Union

import click
from furl import furl

from pyffdl.__version__ import __version__
from pyffdl.sites import (
    AdultFanFictionStory,
    ArchiveOfOurOwnStory,
    FanFictionNetStory,
    HTMLStory,
    TwistingTheHellmouthStory,
)
from pyffdl.utilities import get_url_from_file, list2text

AVAILABLE_SITES = {
    "fanfiction.net": FanFictionNetStory,
    "fictionpress.com": FanFictionNetStory,
    "adult-fanfiction.org": AdultFanFictionStory,
    "archiveofourown.org": ArchiveOfOurOwnStory,
    "tthfanfic.org": TwistingTheHellmouthStory,
}


def download(urls: List[str], update: Union[str, None] = None) -> None:
    for address in urls:
        try:
            host = ".".join(furl(address).host.split(".")[-2:])
            if host in AVAILABLE_SITES.keys():
                _story = AVAILABLE_SITES[host]
                story = _story.from_url(furl(address), update)
                if not update:
                    story.run()
                else:
                    story.update_run()
            else:
                click.echo(
                    f"{__file__} is currently only able to download from {list2text(AVAILABLE_SITES.keys())}."
                )
        except AttributeError as e:
            print(e)
            click.echo("There were problems with parsing the URL.")
            click.echo(
                "This may have been caused by trying to update a file not created by pyffdl."
            )


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass


@cli.command("download", help="Download a new fanfiction story.")
@click.option(
    "-f",
    "--from",
    "from_file",
    type=click.File(),
    help="Load a list of URLs from a plaintext file.",
)
@click.argument("url_list", nargs=-1)
def cli_download(from_file: click.File, url_list: Tuple[str, ...]) -> None:
    urls = [x for x in url_list]
    if from_file:
        urls += [x.strip("\n") for x in from_file.readlines()]
    download(urls)


@cli.command("simple", help="Download a single story, using a list of chapter URLs.")
@click.option(
    "-f",
    "--from",
    "from_file",
    type=click.File(),
    help="Load a list of URLs from a plaintext file.",
)
@click.option("-a", "--author", help="Name of the author", type=str, required=True)
@click.option("-t", "--title", help="Title of the story", type=str, required=True)
@click.argument("url_list", nargs=-1)
def cli_simple(
    from_file: click.File, author: str, title: str, url_list: Tuple[str, ...]
):
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
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Completely refresh the ebook file.",
)
@click.option(
    "-b", "--backup", is_flag=True, default=False, help="Backup the original file."
)
@click.argument("filenames", type=click.Path(dir_okay=False, exists=True), nargs=-1)
def cli_update(force: bool, backup: bool, filenames: List[click.Path]) -> None:
    for filename in filenames:
        update = filename if force else None
        if backup:
            shutil.copy(f"{filename}", f"{filename}.bck")
        download([get_url_from_file(filename)], update)

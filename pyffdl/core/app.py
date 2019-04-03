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


def download(
    urls: List[Tuple[str, Union[str, None]]], verbose: bool = False, force: bool = False
) -> None:
    for address, filename in urls:
        if not address:
            continue
        try:
            host = ".".join(furl(address).host.split(".")[-2:])
            try:
                Story = AVAILABLE_SITES[host]
                story = Story(furl(address), verbose)
                story.force = force
                if filename:
                    story.filename = filename
                story.run()
            except KeyError:
                click.echo(
                    f"{__file__} is currently only able to download from {list2text(AVAILABLE_SITES.keys())}."
                )
        except AttributeError as e:
            print(e)
            error = "There were problems with parsing the URL."
            with open("pyffdl.log", "a") as fp:
                click.echo(error, file=fp)
            click.echo(error, err=True)


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
@click.option("-v", "--verbose", is_flag=True)
@click.argument("url_list", nargs=-1)
def cli_download(
    from_file: click.File, url_list: Tuple[str, ...], verbose: bool = False
) -> None:
    urls = [(x, None) for x in url_list]
    if from_file:
        urls += [(x.strip("\n"), None) for x in from_file.readlines()]
    download(urls, verbose)


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
@click.option("-v", "--verbose", is_flag=True)
@click.argument("url_list", nargs=-1)
def cli_simple(
    from_file: click.File,
    author: str,
    title: str,
    url_list: Tuple[str, ...],
    verbose: bool = False,
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
        verbose=verbose,
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
@click.option("-v", "--verbose", is_flag=True)
@click.argument("filenames", type=click.Path(dir_okay=False, exists=True), nargs=-1)
def cli_update(
    force: bool, backup: bool, filenames: List[click.Path], verbose: bool = False
) -> None:
    if backup:
        for filename in filenames:
            shutil.copy(f"{filename}", f"{filename}.bck")
    stories = [(get_url_from_file(x), str(x) if not force else None) for x in filenames]
    download(stories, verbose, force)

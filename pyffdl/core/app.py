from typing import Tuple

import click
from furl import furl

from pyffdl.__version__ import __version__
from pyffdl.sites import (
    AdultFanFictionStory,
    ArchiveOfOurOwnStory,
    FanFictionNetStory,
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


@click.command()
@click.option("--update", type=click.Path(dir_okay=False, exists=True))
@click.option("--urls", type=click.File())
@click.version_option(version=__version__)
@click.argument("url_list", nargs=-1)
def cli(update: click.Path, urls: click.File, url_list: Tuple[str, ...]) -> None:
    url_list = [x for x in url_list]
    if update:
        url_list.append(get_url_from_file(update))
    if urls:
        url_list += [x.strip("\n") for x in urls.readlines()]
    for address in url_list:
        host = ".".join(furl(address).host.split(".")[-2:])
        if host in AVAILABLE_SITES.keys():
            story = AVAILABLE_SITES[host](address)
            story.run()
        else:
            click.echo(
                f"{__file__} is currently only able to download from {list2text(AVAILABLE_SITES.keys())}."
            )

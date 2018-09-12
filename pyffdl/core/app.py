from typing import Tuple

import click
from furl import furl

from pyffdl.sites import AdultFanFictionStory, FanFictionNetStory, ArchiveOfOurOwnStory
from pyffdl.utilities import get_url_from_file, list2text

AVAILABLE_SITES = {
    "fanfiction.net": FanFictionNetStory,
    "fictionpress.com": FanFictionNetStory,
    "adult-fanfiction.org": AdultFanFictionStory,
    "archiveofourown.org": ArchiveOfOurOwnStory,
}


@click.command()
@click.option("--update", type=click.Path())
@click.option("--urls", type=click.Path())
@click.argument("url_list", nargs=-1)
def cli(update: str, urls: str, url_list: Tuple[str, ...]) -> None:
    url_s = list(url_list)
    if update:
        url_s.append(get_url_from_file(update))
    if urls:
        with open(urls) as url_file:
            for url in url_file.readlines():
                url_s.append(url.strip("\n"))
    for address in url_s:
        host = ".".join(furl(address).host.split(".")[-2:])
        available_url_list = list(AVAILABLE_SITES.keys())
        if host in available_url_list:
            story = AVAILABLE_SITES[host](address)
            story.run()
        else:
            click.echo(
                f"{__file__} is currently only able to download from {list2text(available_url_list)}."
            )

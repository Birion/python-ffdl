#!/usr/bin/env python3

import click
from furl import furl
from typing import Tuple

from ffdl import FanFictionNetStory, AdultFanFictionStory
from ffdl.misc import list2text, get_url_from_file

story_match = {
    "fanfiction.net": FanFictionNetStory,
    "fictionpress.net": FanFictionNetStory,
    "adult-fanfiction.org": AdultFanFictionStory
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
        available_url_list = list(story_match.keys())
        if host in available_url_list:
            story = story_match[host](address)
            story.run()
        else:
            click.echo(__file__ + " is currently only able to download from " + list2text(available_url_list) + ".")


if __name__ == '__main__':
    cli()

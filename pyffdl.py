#!/usr/bin/env python3

import click
from furl import furl
from typing import Tuple

from ffdl import FanFictionNetStory
from ffdl.misc import list2text, get_url_from_file

story_match = {
    "www.fanfiction.net": FanFictionNetStory,
    "www.fictionpress.net": FanFictionNetStory
}


@click.group()
def cli():
    pass


@cli.command()
@click.argument("files", type=click.Path(), nargs=-1)
def update(files: Tuple[str]) -> None:
    addresses = tuple(get_url_from_file(file) for file in files)
    url(addresses)


@cli.command()
@click.argument("url_list", nargs=-1)
def url(url_list: Tuple[str, ...]) -> None:
    for address in url_list:
        parsed_url = furl(address)
        available_urls = list(story_match.keys())
        if parsed_url.host in available_urls:
            story = story_match[parsed_url.host](address)
            story.run()
        else:
            click.echo(__file__ + " is currently only able to download from " + list2text(available_urls) + ".")


if __name__ == '__main__':
    cli()

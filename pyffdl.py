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


@click.command()
@click.option("--update", type=click.Path())
@click.argument("urls", nargs=-1)
def cli(urls: Tuple[str, ...], update: str) -> None:
    urls = list(urls)
    if update:
        urls.append(get_url_from_file(update))
    for address in urls:
        parsed_url = furl(address)
        available_urls = list(story_match.keys())
        if parsed_url.host in available_urls:
            story = story_match[parsed_url.host](address)
            story.run()
        else:
            click.echo(__file__ + " is currently only able to download from " + list2text(available_urls) + ".")


if __name__ == '__main__':
    cli()

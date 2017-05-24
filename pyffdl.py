#!/usr/bin/env python3

import click
from furl import furl

from ffdl import FanFictionNetStory
from ffdl.misc import list2text

story_match = {
    "www.fanfiction.net": FanFictionNetStory,
    "www.fictionpress.net": FanFictionNetStory
}


@click.command()
@click.argument("url")
def cli(url: str) -> None:
    parsed_url = furl(url)
    available_urls = list(story_match.keys())
    if parsed_url.host in available_urls:
        story = story_match[parsed_url.host](url)
        story.run()
    else:
        click.echo(__file__ + " is currently only able to download from " + list2text(available_urls) + ".")


if __name__ == '__main__':
    cli()

#!/usr/bin/env python3

import click
from ffdl import FanFictionNetStory
from ffdl.misc import list2text
from furl import furl

story_match = {
    "www.fanfiction.net": FanFictionNetStory,
    "www.fictionpress.net": FanFictionNetStory
}


@click.command()
@click.argument("url")
def cli(url: str):
    parsed_url = furl(url)
    available_urls = list(story_match.keys())
    if parsed_url.host in available_urls:
        story = story_match[parsed_url.host](parsed_url)
        story.make_ebook()
    else:
        click.echo(__file__ + " is currently only able to download from " + list2text(available_urls) + ".")

if __name__ == '__main__':
    cli()
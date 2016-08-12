#!/usr/bin/env python3
# coding=utf-8

import click
from ffdl import Story


@click.command()
@click.argument("urls", nargs=-1)
def cli(urls: str):
    for url in urls:
        story = Story(url)
        story.make_ebook()

if __name__ == '__main__':
    cli()

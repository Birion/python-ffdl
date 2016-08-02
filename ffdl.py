# coding=utf-8

import click
from ffdl import Story


@click.command()
@click.argument("url")
def cli(url: str):
    story = Story(url)
    story.make_ebook()

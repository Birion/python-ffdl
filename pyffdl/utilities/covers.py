import random
from math import ceil
from pathlib import Path
import re

import attr
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


@attr.s(auto_attribs=True)
class Title:
    text: str
    width: int
    height: int

    @classmethod
    def from_text(cls, text, font):
        return cls(text, *font.getsize_multiline(text))


@attr.s
class Cover:
    image_file: Path = attr.ib()
    font_file: Path = attr.ib()
    text: str = attr.ib()

    _image: Image = attr.ib(init=False)
    _font: ImageFont = attr.ib(init=False)
    _title: Title = attr.ib(init=False)
    _width: int = attr.ib(init=False)
    _height: int = attr.ib(init=False)

    ENHANCERS = [ImageEnhance.Color, ImageEnhance.Sharpness]

    def __attrs_post_init__(self):
        self._image = Image.open(self.image_file)
        self._font = ImageFont.truetype(str(self.font_file), 40)
        self._title = Title.from_text(self.text, self._font)
        self._width, self._height = self._image.size

    def run(self):
        if random.randint(0, 10) % 2:
            self._image = self._enhance()
        self._write()

    @classmethod
    def create(
        cls, title: str, author: str, directory: Path, font: str = "Cormorant-Bold.ttf"
    ):
        cover = random.choice(sorted((directory / "covers").glob("*.jpg")))
        fontfile = directory / "font" / font

        if len(title) > 30:
            words = re.split(r"\s+", title)
            rows = [""]
            for word in words:
                if len(rows[-1]) >= (30 + len(word)):
                    rows.append("")
                rows[-1] += f" {word}"
            rows = [x.strip() for x in rows]
            title = "\n".join(rows)

        text = "\n-\n".join((title, author))
        return cls(cover, fontfile, text)

    def _enhance(self) -> Image:
        enhancer = random.choice(self.ENHANCERS)(self._image)
        return enhancer.enhance(random.randint(5, 8) / 10)

    def _write(self, offset: int = 2) -> None:
        draw = ImageDraw.Draw(self._image)
        fill = "white"
        shadow = "black"

        _x = (self._width - self._title.width) / 2
        _y = (self._height - self._title.height) / 2

        for x in range(-offset, offset + 1):
            for y in range(-offset, offset + 1):
                draw.multiline_text(
                    (_x - x, _y - y),
                    self._title.text,
                    font=self._font,
                    fill=shadow,
                    align="center",
                )

        draw.multiline_text(
            (_x, _y), self._title.text, font=self._font, fill=fill, align="center"
        )

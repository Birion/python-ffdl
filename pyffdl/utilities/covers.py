#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

#  The MIT License (MIT)
#
#  Copyright (c) 2016-2019 Birion
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

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

    image: Image = attr.ib(init=False)
    _font: ImageFont = attr.ib(init=False)
    _title: Title = attr.ib(init=False)
    _width: int = attr.ib(init=False)
    _height: int = attr.ib(init=False)

    ENHANCERS = [ImageEnhance.Color, ImageEnhance.Sharpness]

    def __attrs_post_init__(self):
        self.image = Image.open(self.image_file)
        self._font = ImageFont.truetype(str(self.font_file), 40)
        self._title = Title.from_text(self.text, self._font)
        self._width, self._height = self.image.size

    def run(self):
        if random.randint(0, 10) % 2:
            self.image = self._enhance()
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
        enhancer = random.choice(self.ENHANCERS)(self.image)
        return enhancer.enhance(random.randint(5, 8) / 10)

    def _write(self, offset: int = 2) -> None:
        draw = ImageDraw.Draw(self.image)
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

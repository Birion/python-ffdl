import hashlib
import random
import re
from pathlib import Path

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

    ENHANCERS = [ImageEnhance.Color, ImageEnhance.Sharpness]

    def __attrs_post_init__(self):
        self._image = Image.open(self.image_file)
        self._font = ImageFont.truetype(str(self.font_file), 40)
        self._title = Title.from_text(self.text, self._font)
        self._width, self._height = self._image.size

    def run(self):
        if random.randint(0, 10) % 2:
            self.image = self._enhance()
        self._write()

    @classmethod
    def create(
        cls, title: str, author: str, directory: Path, font: str = "Junction-bold.otf"
    ):
        covers = [x for x in (directory / "covers").glob("*.jpg")]

        text = f"{author} - {title}"

        title_hash = hashlib.md5(text.encode()).hexdigest()
        cover_idx = int(title_hash, base=16) % len(covers)
        cover = covers[cover_idx]

        font_file = directory / "font" / font

        max_width = 20

        if len(title) > max_width:
            words = re.split(r"\s+", title)
            rows = [""]
            for word in words:
                if len(rows[-1]) >= (max_width + len(word)):
                    rows.append("")
                rows[-1] += f" {word}"
            rows = [x.strip() for x in rows]
            title = "\n".join(rows)

        text = f"{author}\n-\n{title}"

        return cls(cover, font_file, text)

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def font(self):
        return self._font

    @property
    def title(self):
        return self._title

    def _enhance(self) -> Image:
        enhancer = random.choice(self.ENHANCERS)(self.image)
        return enhancer.enhance(random.randint(5, 8) / 10)

    def _write(self, offset: int = 2) -> None:
        draw = ImageDraw.Draw(self.image)
        fill = "white"
        shadow = "black"

        _x = (self.width - self.title.width) / 2
        _y = (self.height - self.title.height) / 2

        for x in range(-offset, offset + 1):
            for y in range(-offset, offset + 1):
                draw.multiline_text(
                    (_x - x, _y - y),
                    self.title.text,
                    font=self._font,
                    fill=shadow,
                    align="center",
                )

        draw.multiline_text(
            (_x, _y), self.title.text, font=self.font, fill=fill, align="center"
        )

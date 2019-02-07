import random
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


@attr.s(auto_attribs=True)
class Cover:
    image_file: Path
    font_file: Path
    title: str
    author: str

    ENHANCERS = [ImageEnhance.Color, ImageEnhance.Sharpness]

    def __attrs_post_init__(self):
        self.text = "\n\n".join((self.title, self.author))
        self.image = Image.open(self.image_file)
        self.font = ImageFont.truetype(str(self.font_file), int(800 / len(self.text)))
        self.title = Title.from_text(self.text, self.font)
        self.width, self.height = self.image.size

        if random.randint(0, 10) % 2:
            self.image = self._enhance()

    def run(self):
        self._write()

    @classmethod
    def create(
        cls, title: str, author: str, directory: Path, font: str = "Cormorant-Bold.ttf"
    ):
        cover = random.choice(sorted((directory / "covers").glob("*.jpg")))
        fontfile = directory / "font" / font
        return cls(cover, fontfile, title, author)

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
                    font=self.font,
                    fill=shadow,
                    align="center",
                )

        draw.multiline_text(
            (_x, _y), self.title.text, font=self.font, fill=fill, align="center"
        )

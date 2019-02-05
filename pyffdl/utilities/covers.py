import random
from pathlib import Path

import attr
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


@attr.s(auto_attribs=True)
class Title(object):
    text: str
    width: int
    height: int

    @classmethod
    def from_text(cls, text, font):
        return cls(text, *font.getsize_multiline(text))


def write_text(img: Image, font: ImageFont, title: Title, offset: int = 2) -> None:
    draw = ImageDraw.Draw(img)
    colour_fill = "white"
    colour_shadow = "black"

    width, height = img.size

    _x = (width - title.width) / 2
    _y = (height - title.height) / 2

    for x in range(-offset, offset + 1):
        for y in range(-offset, offset + 1):
            draw.multiline_text((_x - x, _y - y), title.text, font=font, fill=colour_shadow, align="center")

    draw.multiline_text((_x, _y), title.text, font=font, fill=colour_fill, align="center")


def make_cover(datastore: Path, title: str, author: str) -> Image:
    covers_dir = datastore / "covers"
    covers = sorted(covers_dir.glob("*.jpg"))
    cover = random.choice(covers)
    fontname = "Cormorant-Bold.ttf"
    fontfile = datastore / "font" / fontname
    title_text = f"{title}\n\n{author}"

    enhancers = [
        ImageEnhance.Color,
        ImageEnhance.Sharpness,
    ]

    img = Image.open(str(cover))
    fnt = ImageFont.truetype(str(fontfile), int(800 / len(title_text)))

    heading = Title.from_text(title_text, fnt)
    enhancer = random.choice(enhancers)(img)
    if random.randint(0, 10) % 2:
        img = enhancer.enhance(random.randint(5, 8) / 10)
    write_text(img, fnt, heading, 1)

    return img

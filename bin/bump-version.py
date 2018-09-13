#!/usr/bin/env python

import re
from pathlib import Path
from sys import argv, exit

version_file = Path("pyffdl") / "__version__.py"
state_file = Path("version.current")

version_pattern = re.compile(r"^VERSION = \((\d+), ?(\d+), ?(\d+)\)")


def replace_version(text: str, old: list, new: list, sep: str = ".") -> str:
    p_old = sep.join(map(str, old))
    p_new = sep.join(map(str, new))
    return re.sub(p_old, p_new, text)


new_ver = None

try:
    new_ver = [int(x) for x in argv[1].split(".")]
    while len(new_ver) < 3:
        new_ver.append(0)
except IndexError:
    print("Missing new version info")
    exit(1)

with version_file.open() as fp:
    version_text = fp.read()

try:
    old_ver = [int(x) for x in version_pattern.search(version_text).groups()]

    with version_file.open("w") as fp:
        fp.write(replace_version(version_text, old_ver, new_ver, ", "))

    with state_file.open("w") as fp:
        fp.write(".".join(map(str, new_ver)))

except AttributeError:
    print("Couldn't parse __version__.py file. Check and try again!")
    exit(1)

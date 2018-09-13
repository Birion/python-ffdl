#!/usr/bin/env python

from sys import argv

try:
    new_ver = [int(x) for x in argv[1].split(".")]
    while len(new_ver) < 3:
        new_ver.append(0)
    print(".".join(str(x) for x in new_ver))
except IndexError:
    print("Missing new version info")
    exit(1)

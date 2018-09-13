#!/usr/bin/env python

with open("version.current") as fp:
    version = [int(x) for x in fp.read().split(".")]

version[-1] += 1

print(".".join(map(str, version)))

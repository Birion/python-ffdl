#!/usr/bin/env bash

VERSION=$(./bin/fix-version.py ${1})

[[ ${VERSION} ]] && echo ${VERSION} || exit 1

git checkout -b release-${VERSION} dev

./bin/bump-version.py ${VERSION}

git commit -a -m "Bumped version to ${VERSION}"
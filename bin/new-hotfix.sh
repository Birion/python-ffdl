#!/usr/bin/env bash

git checkout master

VERSION=$(./bin/hotfix-version.py)

[[ ${VERSION} ]] && echo ${VERSION} || exit 1

git checkout -b hotfix-${VERSION} master

./bin/bump-version.py ${VERSION}

git commit -a -m "Bumped version to ${VERSION}"
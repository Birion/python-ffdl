#!/usr/bin/env bash

CURRENTVERSION=$(cat version.current)

git checkout master
git merge --no-ff release-${CURRENTVERSION}
git tag -a -m ${CURRENTVERSION} ${CURRENTVERSION}

git checkout dev
git merge --no-ff release-${CURRENTVERSION}

git branch -d release-${CURRENTVERSION}

git push origin dev
git push origin master
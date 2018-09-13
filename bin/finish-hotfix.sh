#!/usr/bin/env bash

CURRENTVERSION=$(cat version.current)

git checkout master
git merge --no-ff hotfix-${CURRENTVERSION}
git tag -a -m ${CURRENTVERSION} ${CURRENTVERSION}

git checkout dev
git merge --no-ff hotfix-${CURRENTVERSION}

git branch -d hotfix-${CURRENTVERSION}

git push origin dev
git push origin master
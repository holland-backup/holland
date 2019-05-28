#!/bin/bash

if [ ${TRAVIS_PULL_REQUEST} = "false" ]
then
   BRANCH=$TRAVIS_BRANCH
else
   BRANCH=$TRAVIS_PULL_REQUEST_BRANCH
fi

docker run --env FORK="https://github.com/holland-backup/holland.git" --env BRANCH=$BRANCH --env DEBUG="True" soulen3/holland:$1

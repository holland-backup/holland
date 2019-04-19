#!/bin/bash
if [ -z "$1" ]; then
    echo "Must pass a version number in form of 'x.y.z'"
    exit 1
fi

full=$1
major=$(echo $1 | awk -F . {' print $1"."$2 '})

find ./ -iname "setup.py" -exec sed -i "s/version = \".*\"/version = \"${full}\"/g" {} \;

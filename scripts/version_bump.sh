#!/bin/bash
if [ -z "$1" ]; then
    echo "Must pass a version number in form of 'x.y.z'"
    exit 1
fi

full=$1
major=$(echo $1 | awk -F . {' print $1"."$2 '})

find ./ -iname "setup.py" -exec sed -i "s/version = '.*'/version = '${full}'/g" {} \;
sed -i "s/version = '.*'/version = '${major}'/g" docs/source/conf.py 
sed -i "s/release = '.*'/version = '${full}'/g" docs/source/conf.py 
sed -i "s/global holland_version .*}/global holland_version ${full}}/g" contrib/holland.spec 

#!/bin/bash

BASEDIR=$(cd $(dirname $0)/../../ && pwd)
STAGING=$BASEDIR/docs/devdocs/staging/

rm -fr $STAGING
mkdir -p $STAGING/holland-core

python generate_modules.py $BASEDIR/holland-core -d $STAGING/holland-core -s rst -m 50

for name in $(cat $BASEDIR/plugins/ACTIVE)
do
    mkdir -p $STAGING/plugins/$name/
    python generate_modules.py $BASEDIR/plugins/$name -d $STAGING/plugins/$name -s rst -m 50
done

echo "OK! Newly generated docs are now in $STAGING"

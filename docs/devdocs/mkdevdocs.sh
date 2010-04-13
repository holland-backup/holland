#!/bin/bash

BASEDIR=$(cd $(dirname $0)/../../ && pwd)

PYTHONPATH="$BASEDIR/holland-core"

for name in $(cat $BASEDIR/plugins/ACTIVE)
do
    PYTHONPATH="$PYTHONPATH:$BASEDIR/plugins/$name"
done

make clean
PYTHONPATH=$PYTHONPATH make html

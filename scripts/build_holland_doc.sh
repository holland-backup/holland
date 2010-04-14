#!/bin/bash
export HOLLAND_SVN_PATH=/root/holland
export HOLLAND_DOC_PATH=/var/www/holland/docs
export PAPER=letter
export http_proxy="http://proxy.dfw1.rackspace.com:3128"

svn update $HOLLAND_SVN_PATH
for BRANCH in `ls $HOLLAND_SVN_PATH/branches`; do
    cd $HOLLAND_SVN_PATH/branches/$BRANCH/docs
    make html latex
    mkdir -p $HOLLAND_DOC_PATH/$BRANCH
    cp -a $HOLLAND_SVN_PATH/branches/$BRANCH/docs/build/html/* $HOLLAND_DOC_PATH/$BRANCH
    cd $HOLLAND_SVN_PATH/branches/$BRANCH/docs/build/latex
    make all-pdf &> /dev/null
    mv Holland.pdf $HOLLAND_DOC_PATH/$BRANCH.pdf
done

for TAG in `ls $HOLLAND_SVN_PATH/tags`; do
    cd $HOLLAND_SVN_PATH/tags/$TAG/docs
    make html latex
    mkdir -p $HOLLAND_DOC_PATH/$TAG
    cp -a $HOLLAND_SVN_PATH/tags/$TAG/docs/build/html/* $HOLLAND_DOC_PATH/$TAG
    cd $HOLLAND_SVN_PATH/tags/$TAG/docs/build/latex
    make all-pdf &> /dev/null
    mv Holland.pdf $HOLLAND_DOC_PATH/$TAG.pdf
done

cd $HOLLAND_SVN_PATH/trunk/docs
make html latex
mkdir -p $HOLLAND_DOC_PATH/trunk
cp -a $HOLLAND_SVN_PATH/trunk/docs/build/html/* $HOLLAND_DOC_PATH/trunk
cd $HOLLAND_SVN_PATH/trunk/docs/build/latex
make all-pdf &> /dev/null
mv Holland.pdf $HOLLAND_DOC_PATH/holland-trunk.pdf

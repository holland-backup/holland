#!/bin/bash

# This scripts generates holland rpms via mock
# Requires: mock rpmdevltools rpm-build

set -o errexit -o nounset

function check_requires() {
    rpm -q rpmdevtools || return 1;
    rpm -q rpm-build || return 1;
    rpm -q mock || return 1
}

check_requires
if [ $? != 0 ]
then
    echo "Missing requirements for building rpms."
    echo "You may need to run: yum install mock rpmdevtools rpmbuild"
fi

echo "Setting up local rpm environment, as needed"
rpmdev-setuptree

SOURCEDIR=$(rpm --eval "%{_sourcedir}")
SRPMDIR=$(rpm --eval "%{_srcrpmdir}")
RPMDIR=$(rpm --eval "%{_rpmdir}")
HOLLAND_VERSION=$(python setup.py --version)
HOLLAND_SRC=$SOURCEDIR/holland-$HOLLAND_VERSION.tar.gz
MOCK_CHROOT=${MOCK_CHROOT:-epel-5-x86_64}

# Export HEAD as the source
echo "Exporting current git tree as tarball to ${HOLLAND_SRC}"
git archive --prefix=holland-$HOLLAND_VERSION/ HEAD > ${HOLLAND_SRC}

# Build a source RPM via mock
echo "Generating holland source rpm via mock"
mock --quiet --root=${MOCK_CHROOT} \
     --buildsrpm \
     --spec=contrib/holland.spec \
     --sources=${SOURCEDIR} \
     --result=${SRPMDIR}
# find the recently generated src rpm
HOLLAND_SRPM=$(ls -t ${SRPMDIR}/holland-${HOLLAND_VERSION}*.src.rpm | head -1)
echo "  Source RPM: ${HOLLAND_SRPM}"

# build the holland rpmset via mock
echo "Generating holland rpm set via mock"
mock --quiet --root=${MOCK_CHROOT} \
     --result=${RPMDIR}/noarch \
     $HOLLAND_SRPM

echo "Finished. The following rpms are available in ${RPMDIR}/noarch/:"
ls ${RPMDIR}/noarch/holland-*1.0.8*.noarch.rpm | xargs -n1 basename

# vim:set ts=4 sw=4 ft=sh et:

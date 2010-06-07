#!/bin/bash
TMPDEV=$(df /tmp | tail -n +2 | head -n 1 | awk '{ print $1; }')
VGNAME='vg_test' TMPDEV=$TMPDEV LVMPATH=/usr/sbin sudo -E python setup.py nosetests -v -v -v -l DEBUG -s < /dev/null

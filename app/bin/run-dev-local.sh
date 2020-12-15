#!/bin/bash

CWD=`pwd`
echo $CWD

CONTENT_ROOT=${1:-$CWD}

echo CONTENT_ROOT $CONTENT_ROOT

cd $CWD/app/client-lib
yarn serve &
P1=$!

$CWD/app/server/main.py -l info -c $CONTENT_ROOT
P2=$!

wait $P1 $P2

cd $CWD
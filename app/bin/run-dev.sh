#!/bin/bash

CWD=`pwd`
echo $CWD

cd $CWD/app/client-lib
yarn serve &
P1=$!

$CWD/app/server/main.py -l info
P2=$!

wait $P1 $P2

cd $CWD
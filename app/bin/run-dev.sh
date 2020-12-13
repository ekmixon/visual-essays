#!/bin/bash

nohup app/server/main.py -l info -c . &
cd app/client-lib
yarn

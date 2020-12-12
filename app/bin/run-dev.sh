#!/bin/bash

cd app/client-lib; yarn; nohup yarn serve & 
cd ../..
app/server/main.py -l info -d -c .

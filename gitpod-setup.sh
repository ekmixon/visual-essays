#!/bin/sh

cd ~
curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-319.0.0-linux-x86_64.tar.gz
tar -vxzf google-cloud-sdk-319.0.0-linux-x86_64.tar.gz
rm -rf google-cloud-sdk-319.0.0-linux-x86_64.tar.gz
export PATH="${PATH}:/workspace/visual-essays/google-cloud-sdk/bin"
# gcloud auth login
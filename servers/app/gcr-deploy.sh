#!/bin/bash

BRANCH=${1:-main}
GCR_SERVICE=visual-essay-exp

/workspace/visual-essays/google-cloud-sdk/bin/gcloud config set project visual-essay

git checkout $BRANCH
rm -rf gcr-build

mkdir gcr-build
cp -va main.py essay.py Dockerfile gcr-build
cp ../../index.html gcr-build
echo ${gh_token} > gcr-build/gh-token

cd gcr-build
/workspace/visual-essays/google-cloud-sdk/bin/gcloud builds submit --tag gcr.io/visual-essay/${GCR_SERVICE}
/workspace/visual-essays/google-cloud-sdk/bin/gcloud beta run deploy ${GCR_SERVICE} --image gcr.io/visual-essay/${GCR_SERVICE} --allow-unauthenticated --platform managed --memory 1Gi

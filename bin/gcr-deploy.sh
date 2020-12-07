#!/bin/bash

BRANCH=${1:-main}
GCR_SERVICE=visual-essay-exp

export PATH="${PATH}:/home/gitpod/google-cloud-sdk/bin"
gcloud config set project visual-essay
gcloud config set compute/region us-central1
gcloud config set run/region us-central1

git checkout $BRANCH
rm -rf gcr-build

cd client-lib
yarn build

cd ..

mkdir -p gcr-build/server
cp -va server/Dockerfile gcr-build
cp -va server/main.py server/essay.py server/gh.py server/sparql server/gh-token gcr-build/server
cp index.html gcr-build
cp -va components gcr-build/components
cp -va static gcr-build/static

cd gcr-build
gcloud builds submit --tag gcr.io/visual-essay/${GCR_SERVICE}
gcloud beta run deploy ${GCR_SERVICE} --image gcr.io/visual-essay/${GCR_SERVICE} --allow-unauthenticated --platform managed --memory 1Gi

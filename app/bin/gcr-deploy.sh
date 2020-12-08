#!/bin/bash

if output="$(git status --porcelain)" && [ -z "$output" ]; then

    VERSION=${1:-main}
    GCR_SERVICE=visual-essay-exp

    export PATH="${PATH}:/home/gitpod/google-cloud-sdk/bin"
    gcloud config set project visual-essay
    gcloud config set compute/region us-central1
    gcloud config set run/region us-central1

    git checkout $BRANCH
    rm -rf gcr-build

    cd app/client-lib
    yarn build

    cd ../..

    mkdir -p gcr-build/server
    cp -va app/Dockerfile gcr-build
    cp -va app/server/*.py app/server/gh-token app/server/*.txt app/server/*.html app/server/sparql gcr-build/server
    cp index.html gcr-build
    HASH=`git rev-parse HEAD | cut -c -7`
    cat index.html | sed "s/APP_VERSION/$VERSION ($HASH)/" > gcr-build/index.html
    cp -va components gcr-build
    cp -va static gcr-build

    cd gcr-build
    #gcloud builds submit --tag gcr.io/visual-essay/${GCR_SERVICE}
    #gcloud beta run deploy ${GCR_SERVICE} --image gcr.io/visual-essay/${GCR_SERVICE} --allow-unauthenticated --platform managed --memory 1Gi

    git checkout main
else
  echo "There are Uncommitted changes. Please commit and try again"
  exit 1
fi
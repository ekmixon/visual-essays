#!/bin/bash

if output="$(git status --porcelain)" && [ -z "$output" ]; then

    VERSION=${1:-main}
    GCR_SERVICE=visual-essay-exp

    CDS=`git log -1 | grep '^Date' | awk '{print $3" "$4" " $6}'`
    COMMIT_DATE=`date -j -f "%b %d %Y" "$CDS" +%Y%m%d`
    COMMIT_HASH=`git log -1 | grep '^commit' | awk '{print $2}' | cut -c -7`
    APP_VERSION="$COMMIT_DATE $COMMIT_HASH"
    echo $APP_VERSION

    export PATH="${PATH}:/home/gitpod/google-cloud-sdk/bin"
    gcloud config set project visual-essay
    gcloud config set compute/region us-central1
    gcloud config set run/region us-central1

    git checkout $VERSION
    rm -rf gcr-build

    cd app/client-lib
    yarn build

    cd ../..

    mkdir -p gcr-build/server
    cp -va app/Dockerfile gcr-build
    cp -va app/server/*.py app/server/gh-token app/server/*.txt app/server/*.html app/server/sparql gcr-build/server
    cp index.html gcr-build
    cat index.html | sed "s/APP_VERSION/$APP_VERSION/" | sed 's/\/visual-essays\/static\//\/static\//' > gcr-build/index.html
    cp -va components gcr-build
    cp -va static gcr-build

    cd gcr-build
    gcloud builds submit --tag gcr.io/visual-essay/${GCR_SERVICE}
    gcloud beta run deploy ${GCR_SERVICE} --image gcr.io/visual-essay/${GCR_SERVICE} --allow-unauthenticated --platform managed --memory 1Gi

    git checkout main
else
  echo "There are Uncommitted changes. Please commit and try again"
  exit 1
fi
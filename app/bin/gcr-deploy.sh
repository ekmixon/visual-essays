#!/bin/bash

if output="$(git status --porcelain)" && [ -z "$output" ]; then

  GCR_SERVICE=${1:-juncture-essays-dev}
  REF=${2:-juncture}

  echo $REF
  git checkout $REF

  CDS=`git log -1 | grep '^Date' | awk '{print $3" "$4" " $6}'`
  COMMIT_DATE=`date -j -f "%b %d %Y" "$CDS" +%Y%m%d`
  COMMIT_HASH=`git log -1 | grep '^commit' | awk '{print $2}' | cut -c -7`
  APP_VERSION="$COMMIT_DATE $COMMIT_HASH"
  echo $APP_VERSION

  export PATH="${PATH}:/home/gitpod/google-cloud-sdk/bin"
  gcloud config set project juncture-essays
  gcloud config set compute/region us-central1
  gcloud config set run/region us-central1

  rm -rf gcr-build

  cd app/client-lib
  yarn build --hash=${COMMIT_HASH}

  cd ../..

  mkdir -p gcr-build/server
  cp -va app/Dockerfile gcr-build
  cp -va app/server/*.py app/server/*.txt app/server/*.html app/server/sparql app/server/mappings gcr-build/server
  cat index.html | sed "s/APP_VERSION/$APP_VERSION/" \
                 | sed 's/\/juncture\/js\//\/static\/js\//' \
                 | sed "s/juncture\.min/juncture.${COMMIT_HASH}.min/" \
                 | sed 's/\/juncture\/app\/client-lib\/public\/css\//\/static\/css\//' > gcr-build/index.html
  cp -va app/client-lib/components gcr-build
  cp -va app/client-lib/public/css gcr-build

  cp -va creds gcr-build
  cp -va js gcr-build
  cp -va images gcr-build

  cd gcr-build
  gcloud builds submit --tag gcr.io/juncture-essays/${GCR_SERVICE}
  gcloud beta run deploy ${GCR_SERVICE} --image gcr.io/juncture-essays/${GCR_SERVICE} --allow-unauthenticated --platform managed --memory 1Gi

  git checkout develop

else
  echo "There are Uncommitted changes. Please commit and try again"
  exit 1
fi
#!/bin/bash
# Only change I made to the DeathStarBench script:
# Don't push to registry
# (might configure to fix this later)
# TODO set paths correctly 

cd $(dirname $0)/..

EXEC="docker buildx"

USER="igorrudyk1"

TAG="latest"

# ENTER THE ROOT FOLDER
cd ../
ROOT_FOLDER=$(pwd)
$EXEC create --name mybuilder --use

for i in hotelreservation
do
  IMAGE=${i}
  echo Processing image ${IMAGE}
  cd $ROOT_FOLDER
  $EXEC build -t "$USER"/"$IMAGE":"$TAG" -f Dockerfile . --platform linux/arm64,linux/amd64 #--push
  cd $ROOT_FOLDER

  echo
done


cd - >/dev/null

#!/bin/bash
# Only change I made to the DeathStarBench script:
# Change user to DOCKER_USER 

cd $(dirname $0)/..

EXEC="docker buildx"

USER=$DOCKER_USER

TAG="latest"

# ENTER THE ROOT FOLDER
cd ../
ROOT_FOLDER=$(pwd)
# TMP hardcoding path
# TODO set paths correctly and parameterize application
ROOT_FOLDER="$USER/CS395T-proposal/bench/DeathStarBench/hotelReservation"
$EXEC create --name mybuilder --use

for i in hotelreservation
do
  IMAGE=${i}
  echo Processing image ${IMAGE}
  cd $ROOT_FOLDER
  $EXEC build -t "$USER"/"$IMAGE":"$TAG" -f Dockerfile . --platform linux/arm64,linux/amd64 --push
  cd $ROOT_FOLDER

  echo
done


cd - >/dev/null

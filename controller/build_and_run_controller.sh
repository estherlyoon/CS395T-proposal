#!/bin/bash
# TODO move this to makefile
docker build -t $DOCKER_USER/controller -f Dockerfile .
docker push $DOCKER_USER/controller
kubectl auth reconcile -f scale_permissions.yaml
kubectl apply -f controller.yaml
#kubectl logs -f clusterconfig

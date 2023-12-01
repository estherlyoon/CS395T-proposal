#!/bin/bash
# TODO move this to makefile
kubectl auth reconcile -f scale_permissions.yaml
kubectl apply -f controller.yaml
#kubectl logs -f clusterconfig

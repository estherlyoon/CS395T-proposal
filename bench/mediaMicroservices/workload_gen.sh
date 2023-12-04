#!/bin/bash
MEDIA_DIR="/root/DeathStarBench/mediaMicroservices"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench default/"${hrclient}":/root
kubectl cp $SCRIPT_DIR/../../bin/wrk/ default/"${hrclient}":/root/wrk
kubectl exec $hrclient -- /bin/bash -c "cd root && ./wrk -D $DIST -t 2 -c 100 -d 20 -L -s ${MEDIA_DIR}/wrk2/scripts/media-microservices/compose-review.lua http://nginx-web-server.esther.svc.cluster.local:8080/wrk2-api/review/compose -R 2000"

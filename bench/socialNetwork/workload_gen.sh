#!/bin/bash
NAMESPACE="esther"
SOCIAL_DIR="/root/DeathStarBench/socialNetwork"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench default/"${hrclient}":/root
kubectl cp $SCRIPT_DIR/../../bin/wrk/ default/"${hrclient}":/root/wrk
kubectl exec $hrclient -- /bin/bash -c "cd root && ./wrk -D exp -t 2 -c 2 -d 20 -L -s ${SOCIAL_DIR}/wrk2/scripts/social-network/compose-post.lua http://nginx-thrift.${NAMESPACE}.svc.cluster.local:8080/wrk2-api/post/compose -R 10"

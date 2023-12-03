#!/bin/bash
NAMESPACE="esther"
SOCIAL_DIR="/root/DeathStarBench/socialNetwork"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench default/"${hrclient}":/root
kubectl exec $hrclient -- /bin/bash -c "cd root && python3 ${SOCIAL_DIR}/scripts/init_social_graph.py --ip=nginx-thrift.${NAMESPACE}.svc.cluster.local --graph=socfb-Reed98" #soc-twitter-follows-mun" # the big one

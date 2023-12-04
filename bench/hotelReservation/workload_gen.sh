#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench default/"${hrclient}":/root
kubectl cp $SCRIPT_DIR/../../bin/wrk/ default/"${hrclient}":/root/wrk
kubectl exec $hrclient -- /bin/bash -c "cd root && ./wrk -D $DIST -t 2 -c 100 -d $DUR -L -s ./DeathStarBench/hotelReservation/wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://frontend-hotelreservation.default.svc.cluster.local:5000 -R 2000"

# -t2 -c100 -d30s -R2000
# kubectl -n hotel-res get ep | grep jaeger-out

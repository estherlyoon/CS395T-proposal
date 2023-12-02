#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench default/"${hrclient}":/root
kubectl cp $SCRIPT_DIR/../bin/wrk/ default/"${hrclient}":/root/wrk
# TODO make general and maybe parameterize (eh)
kubectl exec $hrclient -- /bin/bash -c "cd root && ./wrk -D exp -t 8 -c 16 -d 10 -L -s ./DeathStarBench/hotelReservation/wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://frontend.default.svc.cluster.local:5000 -R 50"

# kubectl -n hotel-res get ep | grep jaeger-out

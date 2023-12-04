#!/bin/bash
MEDIA_DIR="/root/DeathStarBench-fork/mediaMicroservices"
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
hrclient=$(kubectl get pod | grep hr-client- | cut -f 1 -d " ")
kubectl cp $SCRIPT_DIR/../DeathStarBench-fork default/"${hrclient}":/root/DeathStarBench-fork
kubectl exec $hrclient -- /bin/bash -c "cd root && python3 ${MEDIA_DIR}/scripts/write_movie_info.py -c ${MEDIA_DIR}/datasets/tmdb/casts.json -m ${MEDIA_DIR}/datasets/tmdb/movies.json --server_address http://nginx-web-server.default.svc.cluster.local:8080 && ${MEDIA_DIR}/scripts/register_users.sh && ${MEDIA_DIR}/scripts/register_movies.sh"

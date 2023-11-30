#!/bin/bash
kubectl expose deployment jaeger --type=NodePort --name jaeger-service
# Record the NodePort for port 16686
kubectl describe services jaeger-service
# TODO will need a step to find which node is running container when we have >1 worker
# Now, ssh into the node running the jaeger container with:
# `ssh -L 8080:localhost:<NodePort> <worker-hostname>`
# and from your local machine, go to localhost:8080 in your browser

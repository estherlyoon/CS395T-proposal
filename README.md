##Setup Instructions

###Docker
- Login to Docker and add yourself to the `docker` group (`sudo groupadd docker`) so you can use docker without sudo
- Run `make containers` to build the sidecar and init containers and push them to Docker Hub
- Set envvar `DOCKER_USER` to your docker username to configure the deployment script that pulls your built containers

###Minimal Example
The minimal example consists of a single pod running an `nginx` service container alongside a sidecar.
- Perform the Docker setup steps
- Start Kubernetes cluster
```
envsubst < scripts/minimal/deployment.yaml | kubectl apply -f -
```
TODO: Move some of these steps into a bigger Python script to automate running services

###DeathStar HotelReservation###
- Scripting TODO

## Setup Instructions

### Docker
- Login to Docker (docker login) and add yourself to the `docker` group (`sudo usermod -aG docker $USER; newgrp docker`) so you can use docker without sudo
- Set envvar `DOCKER_USER` to your docker username to configure pushing and pulling built containers
- Run `make containers` to build the sidecar and init containers and push them to Docker Hub

### Minimal Example
The minimal example consists of a single deployment running an `nginx` service container alongside a sidecar.
- Perform the Docker setup steps
- Start Kubernetes cluster
```
minikube start
```
- Start the deployment
```
envsubst < scripts/minimal/deployment.yaml | kubectl apply -f -
```
TODO: Move some of these steps into a bigger Python script to automate running services

### DeathStar HotelReservation
- Scripting TODO

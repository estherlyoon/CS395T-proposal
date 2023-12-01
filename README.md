## Setup Instructions

### Installing Dependencies
- Run `bash ./scripts/setup_dependencies.sh'. This script installs Docker Engine, luarocks, lua-socket, and optionally kubectl, and adds your user to the docker group so you can run docker without being root.

### Docker Setup
- Login to Docker (docker login)
- Set envvar `DOCKER_USER` to your docker username to configure pushing and pulling built containers
- Run `make containers` to build the sidecar and init containers and push them to Docker Hub

### Minimal Example
The minimal example consists of a single deployment running an `nginx` service container alongside a sidecar.
- Perform the Docker setup steps
- Start Kubernetes cluster (if one is not already running)
```
minikube start
```
If this gives an error, try:
```
minikube delete --all --purge
minikube start
```
- Start the deployment
```
envsubst < scripts/minimal/nginx.yaml | kubectl apply -f -
envsubst < scripts/minimal/controller.yaml | kubectl apply -f -
```
TODO: Might move some of these steps into a bigger Python script to automate running services

### DeathStar HotelReservation
- Scripting TODO

## Setup Instructions

### Installing Dependencies
- Run `bash ./scripts/setup_dependencies.sh`. This script installs Docker Engine, luarocks, lua-socket, and optionally kubectl, and adds your user to the docker group so you can run docker without being root.

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

### DeathStar HotelReservation
The `run_workload.py` script builds necessary docker images, starts a microservice benchmark and the specified autoscaler, and generated requests. Results are output to `artifacts/latest`. To run:

```
python3 ./scripts/run_workload.py -b hotelReservation
```

#### Exposing jaeger ports
Jaeger lets you visualize microservice traces and a microservice graph. To set it up, run this command on the controller node:
```
kubectl expose deployment jaeger --type=NodePort --name <jaeger-service-name>
```
Save the NodePort for port 16686 that is output from:
```
kubectl describe services <jaeger-service-name>
```
Then, on the node that’s running the jaeger pod, ssh into it to exposse the jaeger port
```
ssh -L 8080:localhost:<saved-NodePort> <worker-hostname>
```
Finally, navigate to localhost:8080 on your local machine (apparently CloudLab machine ports can be exposed to the internet so you can also access it through the CloudLab website).


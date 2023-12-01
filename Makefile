MAKEFILE_PATH := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DEATHSTAR_PATH=$(MAKEFILE_PATH)/DeathStarBench
SIDECAR_PATH=$(MAKEFILE_PATH)/sidecar
CONTROLLER_PATH=$(MAKEFILE_PATH)/controller
BIN=$(MAKEFILE_PATH)/bin

submodule:
	git submodule init
	git submodule update

bin:
	mkdir $(BIN)

wrk: submodule bin
	cd $(DEATHSTAR_PATH)/wrk2 && \
	sudo apt-get install libssl-dev libz-dev -y && make && \
	cp wrk $(BIN) 

containers:
	cd $(SIDECAR_PATH)/init && docker build -t $(DOCKER_USER)/init-iptables -f Dockerfile .
	cd $(SIDECAR_PATH)/proxy && docker build -t $(DOCKER_USER)/sidecar -f Dockerfile .
	cd $(CONTROLLER_PATH)/prometheus && docker build -t $(DOCKER_USER)/controller-prometheus -f Dockerfile .
	docker push $(DOCKER_USER)/init-iptables
	docker push $(DOCKER_USER)/sidecar
	docker push $(DOCKER_USER)/controller-prometheus

clean:
	rm -rf $(BIN) 

clean-kube:
	# Remove any resources in the running cluster 
	kubectl delete all --all --namespace default

start-minimal:
	envsubst < scripts/minimal/deployment.yaml | kubectl apply -f -
	kubectl apply -f scripts/minimal/service.yaml

MAKEFILE_PATH := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DEATHSTAR_PATH=$(MAKEFILE_PATH)/DeathStarBench
SIDECAR_PATH=$(MAKEFILE_PATH)/sidecar
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
	cd $(SIDECAR_PATH)/init && docker build -t $(USER)/init-iptables -f Dockerfile .
	cd $(SIDECAR_PATH)/proxy && docker build -t $(USER)/sidecar -f Dockerfile .
	docker push $(USER)/init-iptables
	docker push $(USER)/sidecar

clean:
	rm -rf $(BIN) 

clean-kube:
	# Remove any resources in the running cluster 
	kubectl delete all --all --namespace default

MAKEFILE_PATH := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
DEATHSTAR=$(MAKEFILE_PATH)/DeathStarBench
BIN=$(MAKEFILE_PATH)/bin

submodule:
	git submodule init
	git submodule update

bin:
	mkdir $(BIN)

wrk: submodule bin
	cd $(DEATHSTAR)/wrk2 && \
	sudo apt-get install libssl-dev libz-dev -y && make && \
	cp wrk $(BIN) 

clean:
	rm -rf $(BIN) 

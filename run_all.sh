#!/bin/bash

#BENCHES=("hotelReservation" "mediaMicroservices" "socialNetwork")
BENCHES=("mediaMicroservices")

for bench in "${BENCHES[@]}"; do
	echo '> Bench $bench'
	echo '> Run 1'
	python3 scripts/run_workload.py -t 5 -d exp -b $bench -s 1s --autoscaler NONE --baseline --build --run 
	echo '> Run 2'
	python3 scripts/run_workload.py -t 5 -d norm -b $bench -s 1s --autoscaler NONE --baseline
	echo '> Run 3'
	python3 scripts/run_workload.py -t 5 -d exp -b $bench -s 1s --autoscaler NONE
	echo '> Run 4'
	python3 scripts/run_workload.py -t 5 -d norm -b $bench -s 1s --autoscaler NONE
	echo '> Run 5'
	python3 scripts/run_workload.py -t 5 -d exp -b $bench -s 1s --autoscaler KHPA
	echo '> Run 6'
	python3 scripts/run_workload.py -t 5 -d norm -b $bench -s 1s --autoscaler KHPA
	echo '> Run 7'
	python3 scripts/run_workload.py -t 5 -d exp -b $bench -s 1s --autoscaler ERL
	echo '> Run 8'
	python3 scripts/run_workload.py -t 5 -d norm -b $bench -s 1s --autoscaler ERL --delete
	echo '--------------------------------- Done ---------------------------------------- '
done

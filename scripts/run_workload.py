import argparse
import subprocess
import time
import os

supported_deathstar = ['hotelReservation']
supported_other = [] #['minimal']

def all_pods_running():
    try:
        result = subprocess.check_output(['kubectl', 'get', 'pods', '--no-headers', '-o', 'custom-columns=:.status.phase'], universal_newlines=True)
        pod_statuses = result.strip().split("\n")

        for status in pod_statuses:
            if status != "Running":
                return False
        return True
    except subprocess.CalledProcessError:
        print("Error executing kubectl")
        exit()

def wait_on_pods():
    while not all_pods_running():
        time.sleep(5)

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"Shell command {cmd} encountered an error:")
            print(res.stderr)
        else:
            print(res.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running shell command {cmd}: {e}")
    except Exception as e:
        print(f"An error occurred running {cmd}: {e}")

def run_deathstar(bench):
    run_cmd('make wrk')

    # Run build script for microservice containers
    # TODO Make build script universal, just need to configure Dockerfile paths
    print("Building Docker images...")
    run_cmd('./scripts/build-docker-images.sh')

    # TODO paths
    print("Starting pods...")
    run_cmd(f'kubectl apply -Rf ./DeathStarBench/{bench}/kubernetes/')
    # Start hr-client
    run_cmd(f'kubectl apply -f ./scripts/hr-client.yaml')

    wait_on_pods()
    print("All pods are running. Generating workload...")
    
    # Generate traffic within cluster through hr-client node
    # TODO make universal
    run_cmd('./scripts/workload_gen.sh')
    print("Done generating workload.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--benchmark', type=str)
    args = parser.parse_args()

    bench = args.benchmark

    # TODO start/stop cluster

    if bench in supported_deathstar:
        run_deathstar(bench) 
    elif bench in supported_other:
        print("Other benchmarks not supported yet.") 
    else:
        supp = ' '.join(supported_deathstar)
        other = ' '.join(supported_other)
        exit(f'Benchmark is not supported.\n \
            > Supported DeathStar benchmarks: {supp} \n \
            > Supported other benchmarks: {other}')


if __name__ == "__main__":
    main()

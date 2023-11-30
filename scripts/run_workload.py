import argparse
import subprocess
import time
import os
from datetime import datetime
import signal

supported_deathstar = ['hotelReservation']
supported_other = [] #['minimal']

supported_autoscalers = ['KHPA']

bench_root = 'artifacts/'
BENCH_DIR = None

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

def kill_process(process):
    try:
        process.terminate()
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()

def wait_on_pods():
    while not all_pods_running():
        time.sleep(5)

def run_background(cmd):
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"Shell command {cmd} encountered an error:")
            print(res.stderr)
        else:
            print(res.stdout)
            return res
    except subprocess.CalledProcessError as e:
        print(f"Error running shell command {cmd}: {e}")
    except Exception as e:
        print(f"An error occurred running {cmd}: {e}")

def get_deployments():
    deployment_res = run_cmd(f'kubectl get deployments')
    deployments = []
    for depl in deployment_res.stdout.splitlines():
        if 'NAME' in depl:
            continue
        deployments.append(depl.split()[0]) 
    return deployments

def delete_hpa():
    deployments = get_deployments()
    for deployment in deployments:
        run_cmd(f'kubectl delete hpa {deployment}')

def delete_autoscaler(autoscaler):
    if autoscaler == 'KHPA':
        delete_hpa()

def run_hpa():
    global BENCH_DIR
    deployments = get_deployments()
    for deployment in deployments:
        run_cmd(f'kubectl autoscale deployment {deployment} --cpu-percent=50 --min=1 --max=10')
    time.sleep(5)
    # Run background process to capture hpa watch output
    out_dir = os.path.join(BENCH_DIR, 'autoscaler.out')
    process = run_background(f'kubectl get hpa --watch | tee -a {out_dir}') 
    return process

def run_autoscaler(autoscaler):
    if autoscaler == 'KHPA':
        return run_hpa()

# TODO Expose jaeger?
def run_deathstar(bench, autoscaler):
    global BENCH_DIR
    run_cmd('make wrk')

    # Run build script for microservice containers
    # TODO Make build script universal, just need to configure Dockerfile paths
    print("Building Docker images...")
    run_cmd('./scripts/build-docker-images.sh')

    # TODO universal paths, need to make DeathStar fork for other benchmarks
    # Fork from the old branch linked in notes
    print("Starting pods...")
    run_cmd(f'kubectl apply -Rf ./DeathStarBench/{bench}/kubernetes/')
    # Start hr-client
    run_cmd(f'kubectl apply -f ./scripts/hr-client.yaml')

    wait_on_pods()
    print("All pods are running.")

    print(f"Enabling {autoscaler} autoscaler...")
    autoscaler_process = run_autoscaler(autoscaler)
    
    # Generate traffic within cluster through hr-client node
    # TODO make universal
    print("Generating workload...")
    gen_res = run_cmd('./scripts/workload_gen.sh')
    print("Done generating workload.")

    # Write workload gen output
    with open(os.path.join(BENCH_DIR, 'workload_gen.out'), 'w') as f:
        f.write(gen_res.stdout)
    with open(os.path.join(BENCH_DIR, 'workload_gen.err'), 'w') as f:
        f.write(gen_res.stderr)

    kill_process(autoscaler_process)
    delete_autoscaler(autoscaler)

# TODO move initialization stuff to section with "init" flag
def main():
    global BENCH_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--benchmark', type=str)
    parser.add_argument('-a', '--autoscaler', type=str, default='KHPA')
    args = parser.parse_args()

    bench = args.benchmark
    autoscaler = args.autoscaler

    if not os.path.exists(bench_root):
        os.mkdir(bench_root)

    # Create directories for output
    timestamp = time.time()
    dt_object = datetime.utcfromtimestamp(timestamp)
    BENCH_DIR = os.path.join(os.getcwd(), bench_root, dt_object.strftime('%Y-%m-%d_%H-%M-%S'))
    os.mkdir(BENCH_DIR)
    print(BENCH_DIR)
    latest_dir = os.path.join(os.getcwd(), bench_root, 'latest')
    print(latest_dir)
    if os.path.islink(latest_dir):
        os.unlink(latest_dir)
    os.symlink(BENCH_DIR, latest_dir)

    if autoscaler not in supported_autoscalers:
        scalers = ' '.join(supported_autoscalers)
        exit(f'Autoscaler {autoscaler} is not supported.\n \
            > Supported autoscalers: {scalers}')

    if bench in supported_deathstar:
        run_deathstar(bench, autoscaler) 
    elif bench in supported_other:
        print("Other benchmarks not supported yet.") 
    else:
        supp = ' '.join(supported_deathstar)
        other = ' '.join(supported_other)
        exit(f'Benchmark is not supported.\n \
            > Supported DeathStar benchmarks: {supp} \n \
            > Supported other benchmarks: {other}')

    # Delete all deployments (have option to keep them up normally, this is for testing) (or should they be cold?)
    run_cmd('kubectl delete deployment --all --namespace=default')
    run_cmd('kubectl delete pod --all --namespace=default')

if __name__ == "__main__":
    main()

import argparse
import subprocess
import time
import os
from datetime import datetime, timedelta
import signal
import yaml
from prometheus_api_client import PrometheusConnect

supported_deathstar = ['hotelReservation', 'mediaMicroservices', 'socialNetwork']
chart_names = {'hotelReservation': 'hotelreservation',
        'mediaMicroservices': 'mediamicroservices',
        'socialNetwork': 'socialnetwork'}
supported_other = [] #['minimal']

supported_autoscalers = ['NONE', 'KHPA', 'ERL']

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

def delete_erl():
    # Don't need to do anything if it's just a pod
    pass

def delete_autoscaler(autoscaler):
    if autoscaler == 'KHPA':
        delete_hpa()
    elif autoscaler == 'ERL':
        delete_erl()
    elif autoscaler == 'NONE':
        pass

def run_hpa(config):
    global BENCH_DIR
    arg_string = ""
    for arg in config['args']:
        arg_string += f" --{list(arg.keys())[0]}={list(arg.values())[0]}"

    deployments = get_deployments()
    for deployment in deployments:
        run_cmd(f'kubectl autoscale deployment {deployment}{arg_string}')
    time.sleep(5)
    # Run background process to capture hpa watch output
    out_dir = os.path.join(BENCH_DIR, 'autoscaler_hpa.out')
    process = run_background(f'kubectl get hpa --watch | tee -a {out_dir}') 
    return process

def run_erl(config):
    return None # We're running controller in main function now

    for arg in config['args']:
        continue

    deployments = get_deployments()
    for deployment in deployments:
        run_cmd(f'envsubst < ./scripts/minimal/controller.yaml | kubectl apply -f -')

    out_dir = os.path.join(BENCH_DIR, 'autoscaler_erl.out')
    process = run_background(f'kubectl logs -f deployment/controller | tee -a {out_dir}') 
    return process

def run_autoscaler(autoscaler, yaml_config):
    config = load_autoscaler_config(yaml_config)
    if autoscaler == 'KHPA':
        return run_hpa(config)
    elif autoscaler == 'ERL':
        return run_erl(config)
    elif autoscaler == 'NONE':
        return None

"""
#expected config:
autoscaler: KHPA
args:
    - arg1: val1
    - arg2: val2
"""
def load_autoscaler_config(config):
    try:
        with open(config, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        config = yaml.safe_load(config)
    return config

# TODO Expose jaeger?
# baseline=True just means we want to measure the runtimes of a cluster with no sidecars attached
def run_deathstar(bench, autoscaler, autoscaler_config, distribution, duration, build=False, run=False, baseline=False, scale='10s'):
    global BENCH_DIR
    if run:
        print("Starting pods with helm...")
        docker_user = os.environ.get('DOCKER_USER')
        if not docker_user:
            exit('Must set envvar DOCKER_USER to docker username')

        deathstar_path = './bench/DeathStarBench' if baseline else './bench/DeathStarBench-fork'
        helm_install = f'''helm install {chart_names[bench]} {deathstar_path}/{bench}/helm-chart/{chart_names[bench]} \\
                        --set global.dockerUser={docker_user}
                        '''
        run_cmd(helm_install)
        run_cmd(f'kubectl apply -f ./bench/hr-client.yaml')
        wait_on_pods()
    else:
        print("Skipping run step.")

    if build:
        # Run build script for microservice containers
        run_cmd('make wrk')
        print("Performing initialization...")
        run_cmd(f'./bench/{bench}/init.sh')
    else:
        print("Skipping build images.")

    # TODO how to change time interval programmatically with HPA?
    if not baseline:
        control = 'TRUE' if autoscaler == 'ERL' else 'FALSE'
        print(f"Running prometheus with DO_CONTROL={control}, SCALE_INTERVAL={scale}...")
        run_cmd(f'DO_CONTROL={control} SCALE_INTERVAL={scale} envsubst < ./scripts/minimal/controller.yaml | kubectl apply -f -')

    wait_on_pods()
    print("All pods are running.")

    print(f"Enabling {autoscaler} autoscaler...")
    autoscaler_process = run_autoscaler(autoscaler, autoscaler_config)

    # Add some buffer to make sure prometheus is up
    #time.sleep(10)
    
    # Generate traffic within cluster through hr-client node
    print("Generating workload...")
    timestamp = time.time()
    dt_object = datetime.utcfromtimestamp(timestamp)
    gen_res = run_cmd(f'DIST={distribution} DUR={duration} ./bench/{bench}/workload_gen.sh')
    print("Done generating workload.")

    # Write workload gen output
    with open(os.path.join(BENCH_DIR, 'workload_gen.out'), 'w') as f:
        f.write(gen_res.stdout)
    with open(os.path.join(BENCH_DIR, 'workload_gen.err'), 'w') as f:
        f.write(gen_res.stderr)

    # Save the controller's output before killing it
    if not baseline:
        controller_out = os.path.join(BENCH_DIR, 'controller.log')
        run_cmd(f'kubectl logs deployments/controller > {controller_out}')

    if autoscaler_process:
        kill_process(autoscaler_process)
    delete_autoscaler(autoscaler)

    return dt_object

def get_prometheus_data(start: datetime, end: datetime, step: str):
    proc = run_background("kubectl port-forward deployment/controller 9090:9090")
    prom = PrometheusConnect()
    
    # get and save inflight requests
    ifr_query = "avg (inflight_requests) by (app)"
    ifr = prom.custom_query_range(ifr_query, start, end, step)

    # get ans save latency
    lat_query = "avg (request_latency) by (app)"
    lat = prom.custom_query_range(lat_query, start, end, step)

    # get and save number of services
    svc_query = "count (inflight_requests) by (app)"
    svc = prom.custom_query_range(svc_query, start, end, step)

    kill_process(proc)

    return ifr, lat, svc
 
def main():
    global BENCH_DIR
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--benchmark', type=str)
    parser.add_argument('-a', '--autoscaler', type=str, default='KHPA')
    parser.add_argument('-d', '--distribution', type=str, default='norm', help='Options for wrk distribution: [norm, exp]')
    parser.add_argument('-t', '--duration', type=str, default='300', help='Duration of workload generation in seconds')
    # Only supported for ERL right now
    parser.add_argument('-s', '--scale-interval', type=str, default='10s', help='Time interval to scale deployments at. Supported: seconds (s) and milliseconds (ms)')
    parser.add_argument('--build', action='store_true', help='If set, will perform init action of building containers')
    parser.add_argument('--run', action='store_true', help='If set, will perform init action of starting deployments')
    parser.add_argument('--delete', action='store_true', help='If set, will perform final action of deleting deployments')
    parser.add_argument('--baseline', action='store_true', help='If set, will run a workload without any sidecars or Prometheus configured (vanilla DeathStar)')
    parser.add_argument('-y', '--yaml', type=str,
        default='{\'autoscaler\': \'KHPA\', \'args\': [{\'cpu-percent\': 50}, {\'min\': 1}, {\'max\': 10}]}',
        help="Either a yaml file path OR a string representing the yaml config for the chosen autoscaler")
    args = parser.parse_args()
    bench = args.benchmark
    autoscaler = args.autoscaler
    yaml = args.yaml

    # Create directories for output
    if not os.path.exists(bench_root):
        os.mkdir(bench_root)

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
    with open(os.path.join(BENCH_DIR, 'config.txt'), 'w') as f:
        config = load_autoscaler_config(yaml)
        baseline = 'true' if args.baseline else 'false'
        f.write(f"benchmark:{args.benchmark}\nautoscaler:{args.autoscaler}\nwrk-dist:{args.distribution}\nwrk-duration:{args.duration}\nscale-interval:{args.scale_interval}\nbaseline:{baseline}\nyaml-config:{config}\n")

    if autoscaler not in supported_autoscalers:
        scalers = ' '.join(supported_autoscalers)
        exit(f'Autoscaler {autoscaler} is not supported.\n \
            > Supported autoscalers: {scalers}')

    if bench in supported_deathstar:
        start_ts = run_deathstar(bench, autoscaler, yaml, args.distribution, args.duration, args.build, args.run, args.baseline, args.scale_interval)
    elif bench in supported_other:
        print("Other benchmarks not supported yet.") 
    else:
        supp = ' '.join(supported_deathstar)
        other = ' '.join(supported_other)
        exit(f'Benchmark is not supported.\n \
            > Supported DeathStar benchmarks: {supp} \n \
            > Supported other benchmarks: {other}')

    if not args.baseline:
        test_len = timedelta(seconds=int(args.duration))
        step = 0.5
        data = get_prometheus_data(start_ts, start_ts + test_len, step)
        print("prometheus output:", data)
        #with open(os.path.join(BENCH_DIR, 'prometheus.log'), 'w') as f:
        #       f.write(data[0])
        #       f.write(data[1])
        #       f.write(data[2])

        run_cmd('kubectl delete deployments/controller')

    if args.delete:
        run_cmd(f'helm uninstall {chart_names[bench]}')
        run_cmd('kubectl delete deployments/hr-client')
        #run_cmd('kubectl delete deployment --all --namespace=default')
        #run_cmd('kubectl delete pod --all --namespace=default')

if __name__ == "__main__":
    main()

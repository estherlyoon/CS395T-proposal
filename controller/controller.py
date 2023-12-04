from __future__ import print_function
from kubernetes import config, client
from kubernetes.client.rest import ApiException
from prometheus_api_client import PrometheusConnect
import time, sys
from datetime import datetime
from typing import Tuple
import os

pod_types = {}
pod_configs = {}
service_queues = {}
pod_queues = {}

def log(string):
    timestamp = time.time()
    dt_object = datetime.utcfromtimestamp(timestamp)
    print(dt_object.strftime('%Y-%m-%d_%H-%M-%S'), string, file=sys.stderr)

def get_node_usage():
    api = client.CustomObjectsApi()
    k8s_nodes = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "nodes")
    for stats in k8s_nodes['items']:
        usage = f"NODE_USAGE Node:{stats['metadata']['name']}, CPU:{stats['usage']['cpu']}, Memory:{stats['usage']['memory']}"
        log(usage)
 
def get_pod_usage():
    api = client.CustomObjectsApi()
    k8s_nodes = api.list_cluster_custom_object("metrics.k8s.io", "v1beta1", "pods")
    deployments = {}
    for stats in k8s_nodes['items']:
        deployment = '-'.join(stats['metadata']['name'].split('-')[:-2])
        if deployment not in deployments:
            deployments[deployment] = [0, 0] #[CPU, MEM]
        cpu = 0
        mem = 0
        for cont in stats['containers']:
            cpu += int(cont['usage']['cpu'].split('n')[0])
            mem += int(cont['usage']['memory'].split('K')[0])
        deployments[deployment][0] += cpu
        deployments[deployment][1] += mem

    for depl, usage in deployments.items():
        usage = f"DEPLOYMENT_USAGE Deployment:{depl}, CPU:{usage[0]}n, Memory:{usage[1]}Ki"
        log(usage)

def get_deployments(namespace='default'):
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace)
    deployments = set()
    for pod in pod_list.items:
        deployment_name = '-'.join(pod.metadata.name.split('-')[:-2])
        deployments.add(deployment_name)
    return list(deployments)

def get_ip_deployment_map(namespace='default'):
    v1 = client.CoreV1Api()
    pod_list = v1.list_namespaced_pod(namespace)
    ip_to_deployment = {}
    for pod in pod_list.items:
        if pod.status.pod_ip in ip_to_deployment:
            print("ERROR pod IP appears twice from list pod command", file=sys.stderr)
        deployment_name = '-'.join(pod.metadata.name.split('-')[:-2])
        ip_to_deployment[pod.status.pod_ip] = deployment_name
    return ip_to_deployment
           
def scale_replicas(name: str, scale: int):
    api_instance = client.AppsV1Api()

    # Get current number of replicas
    curr_replicas = 1
    try:
        read_resp = api_instance.read_namespaced_deployment_scale(name, 'default')
        curr_replicas = read_resp.spec.replicas
    except ApiException as e:
        log("Exception when calling AppsV1Api->read_namespaced_deployment_scale: %s\n" % e)

    if curr_replicas + scale < 1: # TODO parameterize min and max through yaml
        log('min_replicas = 1, not scaling')
        return

    body = {'spec': {'replicas': curr_replicas + scale}}
    try:                                                                        
        scale_resp = api_instance.patch_namespaced_deployment_scale(name, 'default', body)
        log(f"SCALED deployment:{name}, old-replicas:{curr_replicas}, new-replicas:{scale_resp.spec.replicas}")
    except ApiException as e:
        log("Exception when calling AppsV1Api->patch_namespaced_deployment_scale: %s\n" % e)

def get_info_from_prometheus(prom):
    return prom.get_current_metric_value(metric_name="inflight_requests")

def scale_up(queue_length: int) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize latency of service
    return queue_length > 10

def scale_down(queue_length: int) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize number of necessary pods/service
    return queue_length < 2

def convert_to_seconds(time_str):
    try:
        if 'ms' in time_str:
            return float(time_str[:-2]) / 1000
        elif 's' in time_str:
            return float(time_str[:-1])
        else:
            raise ValueError("Invalid time unit. Supported units: 's' (seconds) or 'm' (milliseconds)")
    except ValueError as e:
        print(f"Error: {e}")
    return None

def main():
    if os.environ['DO_CONTROL'] == 'FALSE':
        log('INFO envvar DO_CONTROL=FALSE, not running controller logic.')
        return
    config.load_incluster_config()
    scale_interval = convert_to_seconds(os.environ['SCALE_INTERVAL'])
    if scale_interval is None:
        log('WARNING envvar SCALE_INTERVAL not set, setting to default of 10s')
        scale_interval = 10

    prom = PrometheusConnect(disable_ssl=True)
    print("connected to prometheus", file = sys.stderr)
    print(prom.all_metrics(), file = sys.stderr)
    deployments = get_deployments()
    log("INFO deployments:")
    log(deployments)

    while True:
        status = get_info_from_prometheus(prom)
        print(status, file = sys.stderr)

        # Map from pod IPs -> deployment name
        ip_map = get_ip_deployment_map()

        # Record queue length per pod
        for s in status:
            # We only care about the port exposed by the sidecar
            if ':8000' not in s['metric']['instance']:
                continue
            pod_ip = s['metric']['instance'].split(':')[0]
            service_name = ip_map[pod_ip]
            queue_length = int(s['value'][-1]) # is this right?

            if service_name not in service_queues:
                service_queues[service_name] = queue_length
            else:
                service_queues[service_name] = service_queues[service_name] - pod_queues[pod_ip] + queue_length

            pod_queues[pod_ip] = queue_length
            #log(f'Pod queue for {pod_ip} has length {queue_length}, added to {service_name}')
        
        # Scale replicas per deployment
        for service_name in deployments:
            if service_name not in service_queues:
                if 'controller' not in service_name:
                    log(f'WARNING {service_name} not found in service queues')
                continue
            log(f'CHECK service {service_name}, queue length is {service_queues[service_name]}')
            if scale_up(service_queues[service_name]):
                scale_replicas(service_name, 1)
            elif scale_down(service_queues[service_name]):
                scale_replicas(service_name, -1)

        get_node_usage()
        get_pod_usage()
        time.sleep(scale_interval)

if __name__ == "__main__":
    main()

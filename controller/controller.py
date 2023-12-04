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
            print("Error: pod IP appears twice from list pod command", file=sys.stderr)
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
        log(f"SCALED deployment:{name},old-replicas:{curr_replicas},new-replicas:{scale_resp.spec.replicas}")
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

def main():
    if os.environ['DO_CONTROL'] == 'FALSE':
        return
    config.load_incluster_config()
    # TODO configure through yaml
    scale_interval = 10

    prom = PrometheusConnect(disable_ssl=True)
    print("connected to prometheus", file = sys.stderr)
    print(prom.all_metrics(), file = sys.stderr)
    deployments = get_deployments()
    log("deployments:")
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
            log(f'Pod queue for {pod_ip} has length {queue_length}, added to {service_name}')
        
        # Scale replicas per deployment
        for service_name in deployments:
            if service_name not in service_queues:
                log(f'Error: {service_name} not found in service queue')
                continue
            #log(f'CHECK service {service_name}, queue length is {service_queues[service_name]}')
            if scale_up(service_queues[service_name]):
                scale_replicas(service_name, 1)
            elif scale_down(service_queues[service_name]):
                scale_replicas(service_name, -1)

        time.sleep(scale_interval)

if __name__ == "__main__":
    main()

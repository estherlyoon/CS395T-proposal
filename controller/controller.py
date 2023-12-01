from __future__ import print_function
from kubernetes import config, client
from kubernetes.client.rest import ApiException
import time
from typing import Tuple

pod_types = {}
pod_configs = {}
service_queues = {}
pod_queues = {}

def scale_deployment(name, scale):
    api_instance = client.AppsV1Api()

    # Get current number of replicas
    curr_replicas = 1
    try:
        read_resp = api_instance.read_namespaced_deployment_scale(name, 'default')
        curr_replicas = read_resp['spec']['replicas'] # TODO haven't checked, but smth like this
    except ApiException as e:
        print("Exception when calling AppsV1Api->read_namespaced_deployment_scale: %s\n" % e)

    body = {'spec': {'replicas': curr_replicas+scale}}
    try:                                                                        
        scale_resp = api_instance.patch_namespaced_deployment_scale(name, 'default', body)
        print(scale_resp)
    except ApiException as e:
        print("Exception when calling AppsV1Api->patch_namespaced_deployment_scale: %s\n" % e)

def get_info_from_prometheus():
    # TODO: some kind of http request to get status info
    pass

def scale_up(queue_length: int) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize latency of service
    return queue_length > 10

def scale_down(queue_length: int) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize number of necessary pods/service
    return queue_length < 2

def scale_replicas(num: int, deployment_name: str):
    # TODO: use k8s api to patch deployment to add or remove replica as needed
    pass

def main():
    config.load_incluster_config()
    scale_interval = 10

    while True:
        # TODO: get status from prometheus
        status = get_info_from_prometheus()

        if pod_id not in pod_types:
            # TODO: get pod info from k8s
            pod_types[pod_id] = service_name
            pod_configs[pod_id] = "get me from k8s"
        
        if service_name not in service_queues:
            service_queues[service_name] = queue_length
        else:
            service_queues[service_name] = service_queues[service_name] - pod_queues[pod_id] + queue_length

        pod_queues[pod_id] = queue_length
        if scale_up(service_queues[service_name]):
            scale_deployment(service_name, 1)
        elif scale_down(service_queues[service_name]):
            scale_deployment(service_name, -1)

        time.sleep(scale_interval)

if __name__ == "__main__":
    main()

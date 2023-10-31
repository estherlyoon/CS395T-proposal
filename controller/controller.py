from typing import Tuple

pod_types = {}
pod_configs = {}
service_queues = {}
pod_queues = {}

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
        # TODO: add a new pod of that service
        pass
    elif scale_down(service_queues[service_name]):
        # TODO: remove a pod of that service
        pass


if __name__ == "__main__":
    main()

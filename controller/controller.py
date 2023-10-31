from typing import Tuple
import grpc

pod_types = {}
pod_configs = {}
service_queues = {}
pod_queues = {}

# takes in a message and returns the service name and the queue length of the service
def msg_to_info(msg) -> Tuple[str, str, int]:
    return "service_name", "pod_id", 10

def scale_up(queue_length) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize latency of service
    return queue_length > 10

def scale_down(queue_length) -> bool:
    # want to take into account host resources and queue length
    # trying to minimize number of necessary pods/service
    return queue_length < 2

def main():
    # TODO: receive messages somehow, grpc?
    msg = ""
    service_name, pod_id, queue_length = msg_to_info(msg)

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
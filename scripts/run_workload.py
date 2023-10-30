import argparse
import subprocess
import time

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--benchmark', type=str)
    args = parser.parse_args()

    # TODO run `kubectl apply -Rf <path-of-repo>/hotelReservation/kubernetes/`
    wait_on_pods()

    # Start hr-client if generating (`kubectl apply -f hr-client.yaml`)
    # ^Should this + other stuff just be bash script? have to enter a kubernetes shell


if __name__ == "__main__":
    main()

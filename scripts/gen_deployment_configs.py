import argparse
import yaml

def get_field_values_by_key(data, key):
    results = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                results.append(v)
            results.extend(get_field_values_by_key(v, key))
    elif isinstance(data, list):
        for item in data:
            results.extend(get_field_values_by_key(item, key))
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--yaml', type=str)
    args = parser.parse_args()

    """
    For all yaml files passed in (either in directory or specific file) that are deployments, 
        - add initContainer for iptables
        - add sidecar container, configured with the right port
        - also add SERVICE_PORT env var to both
        - add name label
    how to get right port?

    kind: Deployment
    """

    with open(args.yaml, 'r') as f:
        data = yaml.safe_load(f)
        print(data)
    exit()

    yaml_paths = []
    if os.path.isfile(args.yaml) and args.yaml.endswith('.yaml'):
        yaml_paths.append(input_path)
    elif os.path.isdir(args.yaml):
        yaml_paths.extend(glob.glob(os.path.join(args.yaml, '*.yaml')))
    else:
        print(f"Invalid input: {input_path}")

    for yaml_file in yaml_paths:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            if data['kind'] != 'Deployment':
                continue

            container_ports = get_field_values_by_key(data, 'containerPort')

            sidecar_field = {}

            data['spec']['']



if __name__ == "__main__":
    main()

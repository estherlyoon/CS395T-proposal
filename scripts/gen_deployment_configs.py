import os
import argparse
import yaml
import glob

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
    parser.add_argument('-o', '--outpath', type=str)
    args = parser.parse_args()

    """
    For all yaml files passed in (either in directory or specific file) that are deployments, 
        - add initContainer for iptables
        - add sidecar container, configured with the right port
        - also add SERVICE_PORT env var to both
        - add name label
    """

    yaml_paths = []
    if os.path.isfile(args.yaml) and args.yaml.endswith('.yaml'):
        yaml_paths.append(args.yaml)
    elif os.path.isdir(args.yaml):
        for root, dirs, files in os.walk(args.yaml):
            yaml_paths.extend(glob.glob(os.path.join(root, '*.yaml')))
    else:
        print(f"Invalid input: {args.yaml}")

    for yaml_file in yaml_paths:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            if data['kind'] != 'Deployment':
                continue
            print(yaml_file)

            container_ports = get_field_values_by_key(data, 'containerPort')

            init_field = [{'name': 'init-iptables',
                'image': '${DOCKER_USER}/init-iptables:latest',
                'securityContext': {'capabilities': {'add': ['NET_ADMIN']}, 'privileged': True},
                'env': []}]

            sidecar_field = {'name': 'sidecar',
                    'image': '${DOCKER_USER}/sidecar:latest',
                    'ports': [{'containerPort': 8000}],
                    'env': []}

            # We don't support multiple containerPorts right now
            for port in container_ports[:1]:
                init_field[0]['env'].append({'name': 'SERVICE_PORT', 'value': port})
                sidecar_field['env'].append({'name': 'SERVICE_PORT', 'value': port})

            data['spec']['template']['spec']['initContainers'] = init_field
            data['spec']['template']['spec']['containers'].append(sidecar_field)
            data['metadata']['labels']['app'] = data['metadata']['name']

            with open(os.path.join(args.outpath, 'new_' + os.path.basename(yaml_file)), 'w') as file:
                yaml.dump(data, file, default_flow_style=False)

if __name__ == "__main__":
    main()

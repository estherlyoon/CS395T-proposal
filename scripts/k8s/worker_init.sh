#!/bin/bash
bash install_containerd.sh
bash other_cluster_setup.sh

# MANUAL STEP: you need to specify the token and hash output from `kubeadm init`
# in the controller_init.sh script. You also may need to change the IP/port
# based on the script output. (Just copy the entire join command)
sudo kubeadm join 128.110.218.4:6443 --token <YOUR-TOKEN-HERE> \
		--discovery-token-ca-cert-hash <YOUR-HASH-HERE>

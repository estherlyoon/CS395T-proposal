#!/bin/bash

#bash install_containerd.sh
#bash other_cluster_setup.sh

# CIDR is specified for running with Flannel
# MANUAL STEP: Save the token output from this command
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --cri-socket=/run/containerd/containerd.sock

# To start using your cluster, run the following:
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install Flannel
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# Install Metrics Server (it won't work until you do the rest of the steps in manual_setup.MD)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/high-availability-1.21+.yaml

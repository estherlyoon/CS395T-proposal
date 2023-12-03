#!/bin/bash
sudo apt install -y \
	ca-certificates \
	curl \
	gnupg \
	lsb-release

# Download Docker GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
	"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
	$(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Refresh package index
sudo apt update
sudo apt install containerd.io

# Start containerd
sudo systemctl start containerd
sudo systemctl enable containerd

# Create new config.toml
containerd config default | sudo tee /etc/containerd/config.toml
# Enable using systemd
sudo sed -i 's/SystemdCgroup \= false/SystemdCgroup \= true/g' /etc/containerd/config.toml
# Install CNI
wget https://github.com/containernetworking/plugins/releases/download/v1.1.1/cni-plugins-linux-amd64-v1.1.1.tgz
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.1.1.tgz

# Restart to apply changes
sudo systemctl restart containerd

# Verify installation worked and containerd is running
sudo systemctl status containerd

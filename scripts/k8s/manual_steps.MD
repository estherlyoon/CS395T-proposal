The manual steps you need to do to set up the cluster.

## If setting up the controller ##
```bash controller_init.sh```

To get the metrics server to work:
```kubectl edit deploy -n kube-system metrics-server```

An editor will pop up. Add the following flag under `spec:template:spec:container:args`:

```--kubelet-insecure-tls```

Add `serverTLSBootstrap: true` to the kubelet-config ConfigMap

```kubectl edit cm -n kube-system kubeadm-config```

An editor will pop up. Add the flag here:

```
apiVersion: kubeadm.k8s.io/v1beta3
kind: ClusterConfiguration
---
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
serverTLSBootstrap: true
```

## If setting up a worker ##
```bash worker_init.sh```

Add `serverTLSBootstrap: true` to `/var/lib/kubelet/config.yaml` and restart the kubelet with

```sudo systemctl restart kubelet```

To test that the metrics server is up and running, you can run

```kubectl top pods -n kube-system```

and you can also check the pod status with

```kubectl get pods -nkube-system```

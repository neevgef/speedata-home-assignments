# Speedata - Skywatch Assignment

This repository contains the implementation for the Skywatch home assignment.

## Overview

This repository contains:

- A backend and frontend for a application that gives you the weather in a city of your choice.
- A Ansible + Vagrant script for deploying a K3S cluster.
- A Helm chart to deploy our web application
- A CI Pipeline for linting and building our application, then updating the helm chart to the new version. 
- This ReadMe that will explain how to deploy the application from start to end.

## Assignment Context

The assignment is located in [skywatch-assignment.md](skywatch-assignment.md).

## Deployment

### 1. Provision the Kubernetes cluster

Start with the [cluster-provisioning README](deploy/cluster-provisioning/README.md)
and follow its instructions to create the K3s cluster and configure `kubectl`.
From the repository root, confirm that the cluster is reachable:

```sh
kubectl get nodes
```

The remaining steps assume Helm and `kubectl` are installed and that `kubectl`
is configured to use the target cluster.

### 2. Adding Pull-Secret for Private Repository

1. Go to GitHub `Settings`, then choose `Developer Settings`. Inside choose `Personal Access Tokens` and `Tokens (classic)`. Create a token with the `read:packages` permissions and save it.

2. Create pullsecret Secret:

```bash
kubectl create secret docker-registry github-registry --docker-server=ghcr.io/neevgef --docker-username=neevgef --docker-password=<step-1-token> --docker-email=neevnuv@gmail.com -n skywatch
```

3. Patch default Service Account in skywatch namespace to use this pull secret:

```bash
kubectl patch serviceaccount default -n skywatch -p '{\"imagePullSecrets\": [{\"name\": \"github-registry\"}]}'
```

### 3. Deploy with Helm (without Argo CD)

From the repository root, install or upgrade the SkyWatch chart:

```sh
helm install skywatch ./deploy/helm --namespace skywatch --create-namespace
```

Check that the application pods are ready:

```sh
kubectl get pods,services -n skywatch
```

The frontend is available at `http://<node-ip>:30080`. For the local cluster
created by the provisioning instructions, use `http://192.168.56.10:30080`.

### 4. Deploy with Argo CD

Use this method instead of the direct Helm deployment above. It installs Argo
CD with Helm, then creates the Argo CD Application that tracks this repository
and deploys the chart from `deploy/helm`.

Add the Argo Helm repository and install Argo CD:

```sh
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace
```

Apply the SkyWatch Argo CD Application:

```sh
kubectl apply -f deploy/argo-application.yaml
```

The Application is configured to sync automatically, including pruning removed
resources and correcting drift. Check its status and the deployed workloads:

```sh
kubectl get application skywatch -n argocd
kubectl get pods,services -n default
```

The frontend is available at `http://<node-ip>:30080` (or
`http://192.168.56.10:30080` for the locally provisioned cluster).


### Credits

This was written by Neev Geffen.
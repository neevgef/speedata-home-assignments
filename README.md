# SkyWatch

SkyWatch is a small weather lookup application deployed to a local Kubernetes
cluster. This repository contains the application, its container builds, a
Helm chart, K3s provisioning automation, and GitHub Actions/Argo CD
configuration.

The original assignment is documented in [skywatch-assignment.md](skywatch-assignment.md).
I chose **Path A**: three Ubuntu VMs provisioned with Vagrant and Ansible,
running K3s.

## Architecture

**K8s Architecture**
```text
Browser
  |
  | HTTP
  v
Frontend Service (LoadBalancer, nodePort 30080, port 5000)
  |
  v
Flask frontend (1 replica)
  |
  | HTTP, in-cluster
  v
Backend Service (ClusterIP, port 8000)
  |
  v
FastAPI backend (2 replicas) ---> Open-Meteo geocoding and forecast APIs
```

**CI\CD Architecture**
```text
GitHub Actions ---> GHCR images + image tags in deploy/helm/values.yaml
                                      |
                                      v
                                  Argo CD ---> Helm chart ---> K3s
```

- **Application:** The Flask frontend accepts a city and calls the FastAPI
  backend. The backend resolves the city and current temperature through
  Open-Meteo; no API key is required.
- **Cluster:** Vagrant creates one control-plane VM and two worker VMs.
  Ansible installs the pinned K3s version and configures the nodes. See
  [cluster provisioning](deploy/cluster-provisioning/README.md) for node
  addresses and provisioning details.
- **Packaging:** One Helm chart manages both services. The frontend is exposed
  using a `LoadBalancer` Service; the backend uses an internal `ClusterIP`.
  ConfigMaps provide runtime configuration, and the deployments define health
  probes and CPU/memory requests and limits.
- **Delivery:** The GitHub Actions workflows lint and build the frontend and
  backend images, publish commit-SHA-tagged images to GHCR, and are intended to
  update the image tags in the chart. Argo CD watches `main` and has automated
  sync, pruning, and self-healing enabled in
  [argo-application.yaml](deploy/argo-application.yaml).

## Design decisions

- **Vagrant and VirtualBox** - I was faced to choose between Multipass and Vagrant.
  While Multipass can route through VirtualBox on Windows Home, it is natively built
  to favor Hyper-V. Vagrant has spent over a decade perfecting its integration with 
  Oracle VM VirtualBox. Moreover, in the K3s Ansible documentation, they recommend
  using Vagrant.
- **FastAPI for Backend** - FastAPI is a modern and popular Python web framework
  that has gained significant traction in the web development community. It is known 
  for its exceptional performance and comes with an automatic user-friendly API 
  documentation.
- **Deployments instead of StatefulSets** - Both services are stateless and
  need neither stable pod identities nor persistent per-pod storage. A
  Deployment provides the rollout and replica management these workloads
  require without StatefulSet complexity.
- **Ansible for cluster provisioning** - Keeping K3s installation and node
  configuration in Ansible separates VM creation from software provisioning.
  It makes setup repeatable and easier to rerun or maintain than embedding
  those steps in Vagrant.


## A How-To Guide - Bring up from scratch

### Prerequisites

- Git and a GitHub account with access to this repository and its GHCR packages.
- Docker, VirtualBox, and Vagrant on the Windows host.
- WSL (or another Linux control machine) with Ansible 2.14 or newer and SSH
  access to the Vagrant private network.
- `kubectl` and Helm on the machine from which you manage the cluster.
- About 16 GB of RAM, 20 GB of free disk, and 4 or more CPU cores.

The VM allocation is approximately 2 GB for the control plane and 2.5 GB for
each worker. On Windows, use PowerShell for Vagrant and host-side `kubectl`;
use WSL/Linux for Ansible. If WSL cannot reach the VMs' private IP addresses,
resolve that host/WSL networking issue before running Ansible.

### 1. Get the code

```sh
git clone https://github.com/neevgef/speedata-home-assignments.git
cd speedata-home-assignments
```

### 2. Create and provision the K3s cluster

From PowerShell, start the VMs:

```powershell
Set-Location deploy\cluster-provisioning
vagrant up
vagrant status
```

From WSL/Linux, in the same repository's
`deploy/cluster-provisioning` directory, copy Vagrant's generated SSH keys and
install the Ansible collection used by the playbook:

```sh
mkdir -p ~/.ssh
cp .vagrant/machines/server1/virtualbox/private_key ~/.ssh/server1_private_key
cp .vagrant/machines/agent1/virtualbox/private_key ~/.ssh/agent1_private_key
cp .vagrant/machines/agent2/virtualbox/private_key ~/.ssh/agent2_private_key
chmod 600 ~/.ssh/server1_private_key ~/.ssh/agent1_private_key ~/.ssh/agent2_private_key
ansible-galaxy collection install community.general
ansible-playbook -i inventories/staging/hosts.yaml main.yaml
```

The playbook installs K3s on the control plane before joining the workers. Its
configuration pins the K3s version and selects the private-network interface
for Flannel. The playbook can be rerun after provisioning.

Back in PowerShell, configure the host's kubeconfig and check the nodes:

```powershell
Set-Location deploy\cluster-provisioning
New-Item -ItemType Directory -Force "$HOME\.kube" | Out-Null
vagrant ssh server1 -c "sudo cat /etc/rancher/k3s/k3s.yaml" |
    Set-Content -Encoding ascii "$HOME\.kube\config"
$config = Get-Content "$HOME\.kube\config" -Raw
$config.Replace("https://127.0.0.1:6443", "https://192.168.56.10:6443") |
    Set-Content -Encoding ascii "$HOME\.kube\config"
kubectl get nodes -o wide
```

Keep the kubeconfig and Vagrant SSH keys private; do not commit them.

### 3. Allow the cluster to pull the application images

If the GHCR packages are private, create a GitHub Personal Access Token with
`read:packages`. Create the app namespace, then create a registry Secret and
attach it to that namespace's default ServiceAccount. Run in PowerShell,
substituting your account information. Enter the token into the environment
only for this setup; never put it in a repository file:

```powershell
kubectl create namespace skywatch
$env:GHCR_USERNAME = "<your-github-username>"
$env:GHCR_TOKEN = "<PAT-with-read:packages>"
kubectl create secret docker-registry ghcr-pull `
    --docker-server=ghcr.io `
    --docker-username=$env:GHCR_USERNAME `
    --docker-password=$env:GHCR_TOKEN `
    --docker-email="<your-email>" `
    --namespace=skywatch
kubectl patch serviceaccount default --namespace=skywatch `
    --patch '{"imagePullSecrets":[{"name":"ghcr-pull"}]}'
Remove-Item Env:GHCR_TOKEN
```

The namespace must exist before applying the Argo CD Application: the
Application manifest targets `skywatch` and does not request automatic
namespace creation.

### 4. Install Argo CD and deploy SkyWatch

From the repository root in PowerShell or another shell with Helm and
`kubectl` configured:

```sh
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd --namespace argocd --create-namespace
kubectl apply -f deploy/argo-application.yaml
```

Argo CD will reconcile the `skywatch` Application from the `main` branch.
Check the Application and workloads:

```sh
kubectl get application skywatch -n argocd
kubectl get pods,services -n skywatch
kubectl get application skywatch -n argocd -w
```

We will be able to easily reach our ArgoCD's UI using the command `kubectl port-forward service/argocd-server -n argocd 8080:443` and going to http://localhost:8080

2. Get ArgoCD admin password from secret and decode.

To get encoded secret:

```bash
kubectl get secret -n argocd argocd-initial-admin-secret --template="{{.data.password}}" 
```

Decode Base64 in Linux:

```bash
kubectl get secret -n argocd argocd-initial-admin-secret --template={{.data.password}} | base64 -d
```

Decode Base64 in Windows:

```bash
kubectl get secret -n argocd argocd-initial-admin-secret --template="{{.data.password}}"  > temp.b64
certutil -decode temp.b64 argosecret.txt
type argosecret.txt
```


The frontend Service is `skywatch-frontend`, and its default Service port is
5000. Get the reachable address from the Service's `EXTERNAL-IP`:

```sh
kubectl get service skywatch-frontend -n skywatch -o wide
```

Open `http://<EXTERNAL-IP>:5000`. K3s's ServiceLB should provide the external
address for this local cluster. If the address remains pending, inspect the
Service and K3s ServiceLB pods before troubleshooting connectivity.

### Optional: install directly with Helm

For local chart development only, this can be used instead of the Argo CD
Application. Ensure the namespace and GHCR pull Secret are in place first:

```sh
helm upgrade --install skywatch ./deploy/helm --namespace skywatch
```

For the evaluated GitOps deployment, use Argo CD as described above rather
than managing the same release directly with Helm.

## CI/CD and GitOps Rollout Evidence

A video demonstration of the rollout flow is provided. It shows:

1. The application before changes
2. The ArgoCD application before changes
3. Changing a Header in the frontend's code
4. The GitHub workflow triggering automatically - linting and building the frontend and afterwards updating the image tag in the Helm chart.
5. The ArgoCD application noticing the changes to the Helm Chart and automatically syncing the application.
6. After the Deployment deployed the new pod and terminated the old pod, we see the Header in the app changed from "Skywatch" to "Skywatch - Version 2"

Link to Video - [Code Change CI + ArgoCD Flow](docs/videos/Code-Change-CI-ArgoCD-Flow.mp4)

## Problems encountered and resolutions

- **VMs have more than one network interface:** Flannel could otherwise choose
  the NAT-facing interface, preventing reliable pod networking between VMs.
  The K3s configuration pins Flannel to `enp0s8`, the private-network
  interface. If the VM interface name differs, update `k3s_flannel_iface` in
  `deploy/cluster-provisioning/group_vars/all.yaml`.
- **Node-to-node traffic is filtered:** The playbook adds narrowly scoped UFW
  rules for Flannel VXLAN (UDP 8472), kubelet (TCP 10250), and the Kubernetes
  API from agents to servers (TCP 6443), limited to inventory node addresses.
- **Private image pulls need credentials in the workload namespace:** The
  GHCR pull Secret is created in `skywatch` and referenced by its default
  ServiceAccount. The token is supplied at setup time, not stored in Git.

## What I would improve with more time

- Add automated application tests and metrics/monitoring to each application.
- Add Multi-arch image support at build, using an architecture virtualization tool like QEMU.
- Create an AWS + Terraform installation, in addition to the Vagrant + VirtualBox installation
- Add Prometheus rules to alert on high memory/CPU usage, high error rates, and the availability of the Open-Meteo API for the backend. 

## Tear down

To remove the local VMs, run from `deploy/cluster-provisioning` in PowerShell:

```powershell
vagrant destroy
```

### Credits

Written by Neev Geffen.

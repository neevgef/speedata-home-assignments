# Local K3s Cluster

This directory contains a Vagrant environment and Ansible playbooks for a
three-node K3s cluster:

| Node | Role | Private IP |
| --- | --- | --- |
| `server1` | Control plane | `192.168.56.10` |
| `agent1` | Worker | `192.168.56.11` |
| `agent2` | Worker | `192.168.56.12` |

The K3s version is pinned in `group_vars/all.yaml`. The Ansible roles install
the server first, then join both agents using the server's node token. Re-running
the playbook with the same version and configuration does not reinstall K3s;
configuration changes notify the corresponding service to restart.

## Requirements

- Vagrant and VirtualBox
- Ansible 2.14 or newer on a Linux control machine (for example, WSL)
- SSH network access from Ansible to all three VMs on their private IPs
- `kubectl` on your host, if you want to manage the cluster from the host

On Windows, start and manage the VMs with Vagrant in PowerShell. Run Ansible
from WSL or another Linux environment that can reach the VMs. The private
network must be reachable from that environment.

## 1. Start the VMs

Run the following commands from this directory:

```powershell
vagrant up
vagrant status
```

Vagrant creates one control-plane VM and two worker VMs. Its generated SSH keys
are stored under `.vagrant/machines/<node>/virtualbox/private_key`.

## 2. Prepare SSH keys for Ansible

Ansible connects as the `vagrant` user. Copy each generated key into the
Ansible control machine's `~/.ssh` directory, using the filenames expected by
the playbooks. From this directory in WSL or another Linux shell:

```bash
mkdir -p ~/.ssh
cp .vagrant/machines/server1/virtualbox/private_key ~/.ssh/server1_private_key
cp .vagrant/machines/agent1/virtualbox/private_key ~/.ssh/agent1_private_key
cp .vagrant/machines/agent2/virtualbox/private_key ~/.ssh/agent2_private_key
chmod 600 ~/.ssh/server1_private_key ~/.ssh/agent1_private_key ~/.ssh/agent2_private_key
```

Keep these private keys secure; do not commit or share them.

## 3. Install K3s

From this directory (deploy/cluster-provisioning), run:

```bash
ansible-playbook -i inventories/staging/hosts.yaml main.yaml
```

The playbook installs the control plane before the agents. The agents join
`server1` at `192.168.56.10`. Verify the nodes from the control plane:

```powershell
vagrant ssh server1 -c "sudo k3s kubectl get nodes -o wide"
```

Re-running the command is safe for an unchanged, healthy cluster. If you change
the pinned version or K3s configuration, the relevant service may be
reinstalled or restarted.

## 4. Use kubectl from Windows

After K3s is installed, retrieve its kubeconfig and point it at the control
plane's private IP. Run in PowerShell from this directory:

```powershell
New-Item -ItemType Directory -Force "$HOME\.kube" | Out-Null
vagrant ssh server1 -c "sudo cat /etc/rancher/k3s/k3s.yaml" |
    Set-Content -Encoding ascii "$HOME\.kube\config"
$config = Get-Content "$HOME\.kube\config" -Raw
$config.Replace("https://127.0.0.1:6443", "https://192.168.56.10:6443") |
    Set-Content -Encoding ascii "$HOME\.kube\config"
kubectl get nodes -o wide
```

The kubeconfig grants access to the cluster; keep it private and do not commit
it to Git.

## Tear down

To stop and remove the local VMs, run from this directory:

```powershell
vagrant destroy
```

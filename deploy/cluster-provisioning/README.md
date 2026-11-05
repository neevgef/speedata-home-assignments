# Cluster Provisioning

This guide provisions a three-node K3s cluster locally: one control-plane VM and two worker VMs.

## Table of Contents
[Requirements](#requirements)
[Creating Virtual Machines](#creating-virtual-machines)
[Starting K3s Cluster](#starting-k3s-cluster)

## Requirements
- VirtualBox
- Vagrant
- Ansible (if running on windows install an ansible vm)


## Creating Virtual Machines

Run these commands from *this directory*:

```bash
vagrant up
```

Vagrant creates all three VMs. The machines are assigned static private IPs and can reach one another over the private network.
The private ssh-keys should be saved at `.\deploy\cluster-provisioning\.vagrant\machines\<VM-NAME>\virtualbox\private_key`. Copy then, either to the Ansible VM or your local computer to `./.ssh/<VM-NAME>_private_key`.


## Starting K3s Cluster

Run these commands from this directory after the VMs have started:

```bash
ansible-playbook -i inventories/staging/hosts.yaml main.yaml
```

The staging inventory uses Vagrant's generated SSH keys under `.vagrant/`. The playbook installs the pinned K3s release in `group_vars/all.yaml`; workers join the server at `192.168.56.10`.

The roles skip installation when the exact K3s version is already present. Configuration changes notify a service restart, so an unchanged, healthy cluster is left running on subsequent playbook runs.

To confirm the cluster is ready, run:

```bash
vagrant ssh control-plane -c "sudo k3s kubectl get nodes"
```


This repository contains scripts and Ansible playbook to configure external HTTPS load balancer
for Kubernetes, using `haproxy` with [PROXY Protocol](https://www.haproxy.com/blog/haproxy/proxy-protocol/) enabled.

Repository content requires some configuration to match one's setup, but can be treated as a starting point.

### Rationale

Those scripts were created for extending functionality of my [k3s](https://k3s.io/) cluster. 
K3s ships with a very simple load balancer called [klipper](https://github.com/k3s-io/klipper-lb).
It's effective but fails in two scenarios:

- handling both IPv6 and legacy IPv4 traffic at the same time. Klipper only receives IPv4 traffic. Scripts
  in this repository can configure `haproxy` to receive IPv6 traffic and forward to legacy IPv4 receivers.

- passing client IP address information to the receiving end. Due to usage of `MASQUERADE` in Klipper, original
  IP address information is lost. There's a way to mitigate the problem in general (using `PROXY protocol`) but Klipper
  is too simple to implement it.


### Architecture of the solution

There's a pod running a Python script watching `EndPoint` resources of pods in `traefik` deployment. On startup
and on each change of end points, the script triggers an Ansible playbook to configure HAProxy instances.

Ansible playbook collects EndPoints information, creates `haproxy` configuration on edge nodes and
restart `haproxy` service.

HAProxy listens on port :443 and passes received connections to Traefik pods(s), using TCP loadbalancing
and adding PROXY information to each. TLS certificates are handled by Traefik, there is NO TLS termination
on haproxy.

Optionally, port :80 and unencrypted connections can be passed, too, with PROXY information. Unencrypted
connections are discouraged!


### Setup

#### Networking setup

External `haproxy` is configured to connect directly to `EndPoint`s of `traefik` pods. Therefore
host running `haproxy` needs to be able to access the pod network. How to achieve that depends
heavily on your setup, there's no universal recipe. I suggest using [Wireguard](https://www.wireguard.com/).

If you run `haproxy` on cluster nodes (for IPv6-to-IPv4 ingress), the pods network is already
accessible and no further configuration is needed.


#### Ansible and container image

1. Create an  `ansible/inventory` defining you edge hosts. For each hostname define `haproxy_bind`
   directive, which controls `bind` directive in haproxy config file. For example:

  - `haproxy_bind=ipv6@:443` for receiving IPv6 traffic
  - `haproxy_bind=ipv4@:443` for handling legacy IPv4 connections. Useful for configuring load balancers on hosts
  not being a part of the kubernetes cluster.

  There's also `haproxy_bind_insecure` directive for handling non-encrypted traffic on port 80. It's usage
  is discouraged.

2. Create a pair of SSH keys. Put the public part in `~root/.ssh/authorized_keys` file on edge nodes.

  > ssh-keygen -t ed25519 -C "k8s-haproxy-external-lb_agent" -f ssh_key_agent

  Private part must be accessible for our pod. Create a secret using:

  > kubectl -n kube-system create secret generic haproxy-agent --from-file=ssh_key_agent=ssh_key_agent

3. Pod need to be run with enough permissions to read `EndPoint` resources. Example helm chart
   uses `traefik` service account, which should be already configured on k3s cluster.

4. Build the image:

  > podman build -t registry.example.com/k8s-haproxy-external-lb:version .

   and push to your registry.


#### PROXY protocol receiver

To parse information provided by PROXY protocol, Traefik needs configuration. This is done
using `proxyProtocol.trustedIPs` setting [for entrypoints](https://doc.traefik.io/traefik/routing/entrypoints/#proxyprotocol).

In k3s, you can edit `helmchart traefik` in namespace `kube-system` and add the following:

```yaml
spec:
  valuesContent: |-
    additionalArguments:
      - "--entryPoints.web.proxyProtocol.trustedIPs=198.51.100.1,10.42.0.0/16"
      - "--entryPoints.websecure.proxyProtocol.trustedIPs=198.51.100.1,10.42.0.0/16"
```

The IP range depends on your network configuration. In example above, 10.42.0.0/16 is Kubernetes pod network (for running IPv6-to-IPv4 haproxies) 
and 198.51.100.1 is outgoing address for traffic tuneled from external IPv4 edge node.


### Improvement ideas

* Ansible inventory should probably be turned into a `ConfigMap`
* Configurable `EndPoint`s names, those are hardcoded now for Traefik as shipped with k3s.


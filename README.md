

taugw is an droplet on Digital Ocean. It is connected via 2 wireguard tunnels
to dealt and epsilon (over IPv6 addresses).  It is used to receive IPv4 connections
(mainly/only HTTPS) and tunnel them into tau cluster.

Routing over tunnels (10.42/16 is a k3s pod network):


Traefik helm chart listening to PROXY protocol:
trusted ips 
taugw 192.168.138.9
delta 10.42.3.0
epsilon 10.42.1.0 (?)


Haproxy listens on tau 443/TCP, backends are EndPoints for traefik pods.


Listener listen o EndPoint change, runs ansible to reconfigue HAPROXY on
delta, epsilon (for ipv6 traffic) and taugw-legacy (for ipv4).


ansible requires ansible-collection-community-kubernetes.noarch, ansible-collection-community-general,  python3-openshift.noarch

kubectl -n kube-system get ep traefik -o yaml

subsets:
- addresses:
  - ip: 10.42.4.151
    nodeName: kaitain.pipebreaker.pl
    targetRef:
      kind: Pod
      name: traefik-8569b5b86f-k4wf7
      namespace: kube-system
      resourceVersion: "77184008"
      uid: fc3cfe31-03b2-45b0-a7fb-64301a3cb05d

getting above via ansible:
https://docs.ansible.com/ansible/latest/collections/community/kubernetes/k8s_info_module.html


ssh-keygen -t ed25519 -C "k8s-haproxy-external-lb_agent" -f ssh_key_agent
kubectl -n kube-system create secret generic haproxy-agent --from-file=ssh_key_agent=ssh_key_agent



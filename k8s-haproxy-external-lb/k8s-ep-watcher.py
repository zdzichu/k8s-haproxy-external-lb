#!/usr/bin/python3

import datetime
from kubernetes import client, config as kube_config, watch
import os

NAMESPACE = "kube-system"
NAME = "traefik"

ANSIBLE_INVOCATION="ansible-playbook --diff --user=root --connection paramiko --key-file=/ssh/ssh_key_agent --inventory /ansible-config/inventory /ansible/haproxy-configure.yaml"

# open connection to Kubernetes API
if os.getenv("KUBERNETES_PORT"):
    kube_config.load_incluster_config()
else:
    kube_config.load_kube_config()

# disable error: SSL hostname verification failure
#client.Configuration().assert_hostname = False

k8s_api = client.CoreV1Api()

w = watch.Watch()

# add dummy user until local.py in ansible is fixed
# remove when https://github.com/ansible/ansible/pull/75177 is merged & released
with open('/etc/passwd', 'a') as file:
    file.write(f'default:x:{os.getuid()}:0:default user:/tmp:/sbin/nologin')

print(f"Watching endpoints of '{NAME}' in namespace '{NAMESPACE}'…")

for event in w.stream(func=k8s_api.list_namespaced_endpoints,
        namespace=NAMESPACE,
        field_selector=f"metadata.name={NAME}"):
    print(f"[{datetime.datetime.now().astimezone()}] Event: {event['type']}, {event['object'].kind}: {event['object'].subsets[0].addresses}")
    print(f"Reconfiguring load balancers: {ANSIBLE_INVOCATION} …")
    os.system(ANSIBLE_INVOCATION)
    print("---")

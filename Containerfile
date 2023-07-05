FROM registry.fedoraproject.org/fedora-minimal:38

RUN microdnf install --assumeyes \
	ansible \
	ansible-collection-kubernetes-core \
	python3-paramiko \
	python3-kubernetes \
	python3-jmespath \
	&& microdnf clean all

# needed for ansible getuser() workaround
RUN chmod a+w /etc/passwd

USER 1000

COPY k8s-haproxy-external-lb /app

ADD ansible /ansible

WORKDIR /app

CMD [ "/app/k8s-ep-watcher.py" ]

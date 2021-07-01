FROM fedora:latest

# workaround for running yum in container
USER root

RUN dnf install --assumeyes \
	ansible \
	ansible-collection-community-kubernetes \
	ansible-collection-community-general \
	&& dnf clean all

# needed for ansible getuser() workaround
RUN chmod a+w /etc/passwd

USER 1000

COPY k8s-haproxy-external-lb /app

ADD ansible /ansible

WORKDIR /app

CMD [ "/app/k8s-ep-watcher.py" ]

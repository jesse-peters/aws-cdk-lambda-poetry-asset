# syntax=docker/dockerfile:1.2
FROM python:3.9-slim-bullseye as builder
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y openssh-client git zip

WORKDIR /var/task/
RUN mkdir /root/.ssh && chmod 0700 /root/.ssh && ssh-keyscan -t rsa github.com >> /root/.ssh/known_hosts
COPY ./requirements.txt /var/task/requirements.txt

RUN --mount=type=ssh pip install --target /var/task/ --requirement /var/task/requirements.txt

FROM scratch as scratch
COPY --from=builder /var/task .

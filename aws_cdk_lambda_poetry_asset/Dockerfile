# syntax=docker/dockerfile:1.2
FROM python:3.9-slim-bullseye as builder
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y openssh-client git zip
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

WORKDIR /var/task/
COPY ./requirements.txt /var/task/requirements.txt

RUN --mount=type=ssh pip install --target /var/task/ --requirement /var/task/requirements.txt

FROM scratch as scratch
COPY --from=builder /var/task .

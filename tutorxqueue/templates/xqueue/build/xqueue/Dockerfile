# syntax=docker/dockerfile:1.4
FROM docker.io/ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

# Delete default UID=1000 `ubuntu` user to ensure we can use id 1000 for app user
RUN userdel -r ubuntu

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    apt upgrade -y && \
    apt install -y \
        language-pack-en \
        git \
        python3 \
        python3-pip \
        python3-venv \
        libmysqlclient-dev \
        pkg-config
RUN ln -s /usr/bin/python3 /usr/bin/python

###### Git-clone xqueue repo ######
ARG APP_USER_ID=1000
RUN useradd --home-dir /openedx --create-home --shell /bin/bash --uid ${APP_USER_ID} app
USER ${APP_USER_ID}

RUN git clone {{ XQUEUE_REPOSITORY }} --branch {{ XQUEUE_REPOSITORY_VERSION }} --depth 1 /openedx/xqueue
WORKDIR /openedx/xqueue

###### Install python venv ######
RUN python -m venv /openedx/venv
ENV PATH=/openedx/venv/bin:${PATH}
# https://pypi.org/project/setuptools/
# https://pypi.org/project/pip/
# https://pypi.org/project/wheel/
RUN --mount=type=cache,target=/openedx/.cache/pip,sharing=shared pip install setuptools==75.2.0 pip==24.2 wheel==0.44.0
RUN --mount=type=cache,target=/openedx/.cache/pip,sharing=shared pip install -r requirements.txt
RUN --mount=type=cache,target=/openedx/.cache/pip,sharing=shared pip install uwsgi==2.0.25.1

RUN mkdir /openedx/data /openedx/data/media

EXPOSE 8000
CMD uwsgi \
    --static-map /media=/openedx/data/media/ \
    --http 0.0.0.0:8000 \
    --thunder-lock \
    --single-interpreter \
    --enable-threads \
    --processes=2 \
    --wsgi-file xqueue/wsgi.py

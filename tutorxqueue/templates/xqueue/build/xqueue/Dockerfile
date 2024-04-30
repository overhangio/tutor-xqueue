# syntax=docker/dockerfile:1.4
###### Minimal image with base system requirements for most stages ######
FROM docker.io/python:3.12-slim-bookworm

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update && \
    apt upgrade -y && \
    apt install -y \
        locales \
        git \
        python3-dev \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config && \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LC_ALL en_US.UTF-8

###### Git-clone xqueue repo ######
ARG APP_USER_ID=1000
RUN useradd --home-dir /openedx --create-home --shell /bin/bash --uid ${APP_USER_ID} app
USER ${APP_USER_ID}

RUN git clone {{ XQUEUE_REPOSITORY }} --branch {{ XQUEUE_REPOSITORY_VERSION }} --depth 1 /openedx/xqueue
WORKDIR /openedx/xqueue

###### Install python venv ######
RUN python -m venv /openedx/venv
ENV PATH /openedx/venv/bin:${PATH}
# https://pypi.org/project/setuptools/
# https://pypi.org/project/pip/
# https://pypi.org/project/wheel/
RUN --mount=type=cache,target=/openedx/.cache/pip,sharing=shared pip install setuptools==69.2.0 pip==24.0 wheel==0.43.0
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

FROM docker.io/ubuntu:20.04
MAINTAINER Overhang.io <contact@overhang.io>

RUN apt update && \
  apt upgrade -y && \
  apt install -y language-pack-en git python3 python3-pip python3-venv libmysqlclient-dev
RUN ln -s /usr/bin/python3 /usr/bin/python

ARG APP_USER_ID=1000
RUN useradd --home-dir /openedx --create-home --shell /bin/bash --uid ${APP_USER_ID} app
USER ${APP_USER_ID}

RUN git clone https://github.com/edx/xqueue --branch {{ OPENEDX_COMMON_VERSION }} --depth 1 /openedx/xqueue
WORKDIR /openedx/xqueue

RUN python -m venv /openedx/venv
ENV PATH /openedx/venv/bin:${PATH}
RUN pip install --upgrade pip setuptools
RUN pip install -r requirements.txt
RUN pip install uwsgi==2.0.20

RUN mkdir /openedx/data /openedx/data/media

EXPOSE 8000
CMD uwsgi \
    --static-map /media=/openedx/media/ \
    --http 0.0.0.0:8000 \
    --thunder-lock \
    --single-interpreter \
    --enable-threads \
    --processes=2 \
    --wsgi-file xqueue/wsgi.py

FROM docker.io/ubuntu:20.04
MAINTAINER Overhang.io <contact@overhang.io>

RUN apt update && \
  apt upgrade -y && \
  apt install -y language-pack-en git python3 python3-pip libmysqlclient-dev
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN mkdir /openedx /openedx/data /openedx/data/media
RUN git clone https://github.com/edx/xqueue --branch {{ OPENEDX_COMMON_VERSION }} --depth 1 /openedx/xqueue
WORKDIR /openedx/xqueue

RUN pip install -r requirements.txt
RUN pip install uwsgi==2.0.19.1

EXPOSE 8000
CMD uwsgi \
    --static-map /media=/openedx/media/ \
    --http 0.0.0.0:8000 \
    --thunder-lock \
    --single-interpreter \
    --enable-threads \
    --processes=2 \
    --wsgi-file xqueue/wsgi.py

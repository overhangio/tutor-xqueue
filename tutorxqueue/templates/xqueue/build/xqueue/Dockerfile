FROM docker.io/ubuntu:20.04
MAINTAINER Overhang.io <contact@overhang.io>

RUN apt update && \
  apt upgrade -y && \
  apt install -y language-pack-en git python3 python3-pip libmysqlclient-dev
RUN ln -s /usr/bin/python3 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip

RUN mkdir /openedx /openedx/data
RUN git clone https://github.com/edx/xqueue --branch {{ OPENEDX_COMMON_VERSION }} --depth 1 /openedx/xqueue
WORKDIR /openedx/xqueue

RUN pip install -r requirements.txt

EXPOSE 8000
CMD gunicorn --workers=2 --name xqueue --bind=0.0.0.0:8000 --max-requests=1000 xqueue.wsgi:application

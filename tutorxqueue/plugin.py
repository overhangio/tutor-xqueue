from glob import glob
import os

import pkg_resources

from .__about__ import __version__


config = {
    "add": {
        "AUTH_PASSWORD": "{{ 8|random_string }}",
        "MYSQL_PASSWORD": "{{ 8|random_string }}",
        "SECRET_KEY": "{{ 24|random_string }}",
    },
    "defaults": {
        "VERSION": __version__,
        "DOCKER_IMAGE": "overhangio/openedx-xqueue:{{ XQUEUE_VERSION }}",
        "AUTH_USERNAME": "lms",
        "MYSQL_DATABASE": "xqueue",
        "MYSQL_USERNAME": "xqueue",
    },
}

templates = pkg_resources.resource_filename("tutorxqueue", "templates")
hooks = {
    "init": ["mysql", "xqueue"],
    "build-image": {"xqueue": "{{ XQUEUE_DOCKER_IMAGE }}"},
    "remote-image": {"xqueue": "{{ XQUEUE_DOCKER_IMAGE }}"},
}


def patches():
    all_patches = {}
    for path in glob(
        os.path.join(pkg_resources.resource_filename("tutorxqueue", "patches"), "*")
    ):
        with open(path) as patch_file:
            name = os.path.basename(path)
            content = patch_file.read()
            all_patches[name] = content
    return all_patches

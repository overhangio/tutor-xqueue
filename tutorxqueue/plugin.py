from glob import glob
import json
import os

import click
import pkg_resources
import requests

from tutor import config as tutor_config
from tutor.exceptions import TutorError

from .__about__ import __version__


config = {
    "add": {
        "AUTH_PASSWORD": "{{ 8|random_string }}",
        "MYSQL_PASSWORD": "{{ 8|random_string }}",
        "SECRET_KEY": "{{ 24|random_string }}",
    },
    "defaults": {
        "VERSION": __version__,
        "AUTH_USERNAME": "lms",
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}overhangio/openedx-xqueue:{{ XQUEUE_VERSION }}",
        "HOST": "xqueue.{{ LMS_HOST }}",
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


@click.group(help="Interact with the Xqueue server")
def command():
    pass


@click.group(help="List and grade submissions")
@click.pass_obj
@click.option("-q", "--queue", default="openedx", show_default=True, help="Queue name")
@click.option(
    "-u",
    "--url",
    envvar="TUTOR_XQUEUE_URL",
    help=(
        "Xqueue server base url. By default, this value will be defined from "
        "the plugin configuration. Alternatively, this value can be defined "
        "from the TUTOR_XQUEUE_URL environment variable."
    ),
)
def submissions(context, queue, url):
    context.queue = queue
    context.url = url


@click.command(name="count", help="Count submissions in queue")
@click.pass_obj
def count_submissions(context):
    print_result(context, "count_submissions", context.queue)


@click.command(name="show", help="Show last submission")
@click.pass_obj
def show_submission(context):
    print_result(context, "show_submission", context.queue)


@click.command(name="grade", help="Grade a specific submission")
@click.argument("submission_id")
@click.argument("submission_key")
@click.argument("grade", type=click.FLOAT)
@click.argument("correct", type=click.BOOL)
@click.argument("message")
@click.pass_obj
def grade_submission(context, submission_id, submission_key, grade, correct, message):
    print_result(
        context,
        "grade_submission",
        submission_id,
        submission_key,
        grade,
        correct,
        message,
    )


def print_result(context, client_func_name, *args, **kwargs):
    user_config = tutor_config.load(context.root)
    client = Client(user_config, url=context.url)
    func = getattr(client, client_func_name)
    result = func(*args, **kwargs)
    print(json.dumps(result, indent=2))


class Client:
    def __init__(self, user_config, url=None):
        self._session = None
        self.username = user_config["XQUEUE_AUTH_USERNAME"]
        self.password = user_config["XQUEUE_AUTH_PASSWORD"]

        self.base_url = url
        if not self.base_url:
            scheme = "https" if user_config["ENABLE_HTTPS"] else "http"
            host = user_config["XQUEUE_HOST"]
            self.base_url = "{}://{}".format(scheme, host)
        self.login()

    @property
    def session(self):
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def url(self, endpoint):
        # Don't forget to add a trailing slash to all endpoints: this is how xqueue
        # works...
        return self.base_url + endpoint

    def login(self):
        response = self.request(
            "/xqueue/login/",
            method="POST",
            data={"username": self.username, "password": self.password},
        )
        message = response.get("content")
        if message != "Logged in":
            raise TutorError(
                "Could not login to xqueue server at {}. Response: '{}'".format(
                    self.base_url, message
                )
            )

    def show_submission(self, queue):
        response = self.request("/xqueue/get_submission/", params={"queue_name": queue})
        if response["return_code"] != 0:
            return response
        data = json.loads(response["content"])
        header = json.loads(data["xqueue_header"])
        submission_body = json.loads(data["xqueue_body"])
        submission_id = header["submission_id"]
        submission_key = header["submission_key"]
        submission_files = {}
        for filename, path in json.loads(data["xqueue_files"]).items():
            if not path.startswith("http"):
                # Relative path: prepend with server url
                path = self.base_url + "/" + path
            submission_files[filename] = path
        return {
            "id": submission_id,
            "key": submission_key,
            "body": submission_body,
            "files": submission_files,
            "return_code": response["return_code"],
        }

    def count_submissions(self, queue):
        return self.request("/xqueue/get_queuelen/", params={"queue_name": queue})

    def grade_submission(self, submission_id, submission_key, grade, correct, msg):
        return self.request(
            "/xqueue/put_result/",
            method="POST",
            data={
                "xqueue_header": json.dumps(
                    {"submission_id": submission_id, "submission_key": submission_key}
                ),
                "xqueue_body": json.dumps(
                    {"correct": correct, "score": grade, "msg": msg}
                ),
            },
        )

    def request(self, endpoint, method="GET", data=None, params=None):
        func = getattr(self.session, method.lower())
        response = func(self.url(endpoint), data=data, params=params)
        # TODO handle errors >= 400 and non-parsable json responses
        return response.json()


submissions.add_command(count_submissions)
submissions.add_command(show_submission)
submissions.add_command(grade_submission)
command.add_command(submissions)

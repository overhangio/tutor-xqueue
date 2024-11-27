from __future__ import annotations

import json
import os
from glob import glob
from typing import Any, Literal, Optional, Union

import click
import importlib_resources
import requests  # type: ignore
from tutor import config as tutor_config
from tutor import exceptions
from tutor import hooks as tutor_hooks
from tutor.__about__ import __version_suffix__

from .__about__ import __version__

# Handle version suffix in main mode, just like tutor core
if __version_suffix__:
    __version__ += "-" + __version_suffix__

config: dict[str, dict[str, Any]] = {
    "defaults": {
        "VERSION": __version__,
        "AUTH_USERNAME": "lms",
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}overhangio/openedx-xqueue:{{ XQUEUE_VERSION }}",
        "HOST": "xqueue.{{ LMS_HOST }}",
        "MYSQL_DATABASE": "xqueue",
        "MYSQL_USERNAME": "xqueue",
        "REPOSITORY": "https://github.com/openedx/xqueue",
        "REPOSITORY_VERSION": "{{ OPENEDX_COMMON_VERSION }}",
    },
    "unique": {
        "AUTH_PASSWORD": "{{ 8|random_string }}",
        "MYSQL_PASSWORD": "{{ 8|random_string }}",
        "SECRET_KEY": "{{ 24|random_string }}",
    },
}

# Initialization hooks
# For each service that needs to be initialized, we load the task template
# and add it to the CLI_DO_INIT_TASKS filter, which tells Tutor to
# run it as part of the `init` job.
for service in ["mysql", "xqueue"]:
    full_path: str = str(
        importlib_resources.files("tutorxqueue")
        / "templates"
        / "xqueue"
        / "tasks"
        / service
        / "init"
    )
    with open(full_path, encoding="utf-8") as init_task_file:
        init_task: str = init_task_file.read()
    tutor_hooks.Filters.CLI_DO_INIT_TASKS.add_item((service, init_task))

# Image management
tutor_hooks.Filters.IMAGES_BUILD.add_item(
    (
        "xqueue",
        ("plugins", "xqueue", "build", "xqueue"),
        "{{ XQUEUE_DOCKER_IMAGE }}",
        (),
    )
)

tutor_hooks.Filters.IMAGES_PULL.add_item(
    (
        "xqueue",
        "{{ XQUEUE_DOCKER_IMAGE }}",
    )
)
tutor_hooks.Filters.IMAGES_PUSH.add_item(
    (
        "xqueue",
        "{{ XQUEUE_DOCKER_IMAGE }}",
    )
)


@tutor_hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_xqueue(volumes: list[tuple[str, str]], name: str) -> list[tuple[str, str]]:
    """
    When mounting xqueue with `--mount=/path/to/xqueue`,
    bind-mount the host repo in the xqueue container.
    """
    if name == "xqueue":
        path = "/openedx/xqueue"
        volumes += [
            ("xqueue", path),
            ("xqueue-job", path),
        ]
    return volumes


@click.group(help="Interact with the Xqueue server", name="xqueue")
def command() -> None:
    pass


@click.group(help="list and grade submissions")
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
def submissions(context: click.Context, queue: str, url: str) -> None:
    context.queue = queue  # type: ignore
    context.url = url  # type: ignore


@click.command(name="count", help="Count submissions in queue")
@click.pass_obj
def count_submissions(context: click.Context) -> None:
    print_result(context, "count_submissions", context.queue)  # type: ignore


@click.command(name="show", help="Show last submission")
@click.pass_obj
def show_submission(context: click.Context) -> None:
    print_result(context, "show_submission", context.queue)  # type: ignore


@click.command(name="grade", help="Grade a specific submission")
@click.argument("submission_id")
@click.argument("submission_key")
@click.argument("grade", type=click.FLOAT)
@click.argument("correct", type=click.BOOL)
@click.argument("message")
@click.pass_obj
def grade_submission(
    context: click.Context,
    submission_id: str,
    submission_key: str,
    grade: str,
    correct: str,
    message: str,
) -> None:
    print_result(
        context,
        "grade_submission",
        submission_id,
        submission_key,
        grade,
        correct,
        message,
    )


def print_result(
    context: click.Context,
    client_func_name: str,
    *args: Any,
    **kwargs: Any,
) -> None:
    user_config = tutor_config.load(context.root)  # type: ignore
    client = Client(user_config, url=context.url)  # type: ignore
    func = getattr(client, client_func_name)
    result = func(*args, **kwargs)
    print(json.dumps(result, indent=2))


class Client:
    def __init__(self, user_config: dict[str, Any], url: str = "") -> None:
        self._session: Optional[requests.Session] = None
        self.username = user_config["XQUEUE_AUTH_USERNAME"]
        self.password = user_config["XQUEUE_AUTH_PASSWORD"]

        self.base_url = url
        if not self.base_url:
            scheme = "https" if user_config["ENABLE_HTTPS"] else "http"
            host = user_config["XQUEUE_HOST"]
            self.base_url = f"{scheme}://{host}"
        self.login()

    @property
    def session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def url(self, endpoint: str) -> str:
        # Don't forget to add a trailing slash to all endpoints: this is how xqueue
        # works...
        return self.base_url + endpoint

    def login(self) -> None:
        response = self.request(
            "/xqueue/login/",
            method="POST",
            data={"username": self.username, "password": self.password},
        )
        message = response.get("content")
        if message != "Logged in":
            raise exceptions.TutorError(
                f"Could not login to xqueue server at {self.base_url}. Response: '{message}'"
            )

    def show_submission(self, queue: str) -> Union[dict[str, Any], Any]:
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

    def count_submissions(self, queue: str) -> Any:
        return self.request("/xqueue/get_queuelen/", params={"queue_name": queue})

    def grade_submission(
        self,
        submission_id: str,
        submission_key: str,
        grade: str,
        correct: bool,
        msg: str,
    ) -> Any:
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

    def request(
        self,
        endpoint: str,
        method: str = "GET",
        data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        func = getattr(self.session, method.lower())
        response = func(self.url(endpoint), data=data, params=params)
        # TODO handle errors >= 400 and non-parsable json responses
        return response.json()


submissions.add_command(count_submissions)
submissions.add_command(show_submission)
submissions.add_command(grade_submission)
command.add_command(submissions)

# Add the "templates" folder as a template root
tutor_hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    str(importlib_resources.files("tutorxqueue") / "templates")
)
# Render the "build" and "apps" folders
tutor_hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("xqueue/build", "plugins"),
        ("xqueue/apps", "plugins"),
    ],
)
# Load patches from files
for path in glob(str(importlib_resources.files("tutorxqueue") / "patches" / "*")):
    with open(path, encoding="utf-8") as patch_file:
        tutor_hooks.Filters.ENV_PATCHES.add_item(
            (os.path.basename(path), patch_file.read())
        )

# Add cli commands filter
tutor_hooks.Filters.CLI_COMMANDS.add_item(command)

# Add configuration entries
tutor_hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"XQUEUE_{key}", value) for key, value in config.get("defaults", {}).items()]
)
tutor_hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"XQUEUE_{key}", value) for key, value in config.get("unique", {}).items()]
)
tutor_hooks.Filters.CONFIG_OVERRIDES.add_items(
    list(config.get("overrides", {}).items())
)


########################################
# Xqueue Public Host
########################################


@tutor_hooks.Filters.APP_PUBLIC_HOSTS.add()
def _xqueue_public_hosts(
    hosts: list[str], context_name: Literal["local", "dev"]
) -> list[str]:
    if context_name == "dev":
        hosts += ["{{ XQUEUE_HOST }}:8000"]
    else:
        hosts += ["{{ XQUEUE_HOST }}"]
    return hosts

from .settings import *

ALLOWED_HOSTS = [
    "{{ XQUEUE_HOST }}",
    "xqueue",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "HOST": "{{ MYSQL_HOST }}",
        "PORT": {{ MYSQL_PORT }},
        "NAME": "{{ XQUEUE_MYSQL_DATABASE }}",
        "USER": "{{ XQUEUE_MYSQL_USERNAME }}",
        "PASSWORD": "{{ XQUEUE_MYSQL_PASSWORD }}",
        "OPTIONS": {"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",},
    }
}

LOGGING = get_logger_config(log_dir="/openedx/data/", logging_env="tutor", dev_env=True)
LOGGING["loggers"][""]["handlers"].append("console")
LOGGING["loggers"]["submission_queue.management.commands.run_consumer"] = {
    "level": "WARN",
    "handlers": ["console"]
}

SECRET_KEY = "{{ XQUEUE_SECRET_KEY }}"

USERS = {"{{ XQUEUE_AUTH_USERNAME }}": "{{ XQUEUE_AUTH_PASSWORD}}"}
XQUEUES = {"openedx": None}

{{ patch("xqueue-settings") }}

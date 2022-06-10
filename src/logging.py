import logging
from logging.config import dictConfig
from flask import has_request_context, request


class ExFormatter(logging.Formatter):
    def_keys = [
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    ]

    def format(self, record):
        string = super().format(record)
        extra = {k: v for k, v in record.__dict__.items() if k not in self.def_keys}

        if has_request_context():
            extra["url"] = request.url
            extra["remote_addr"] = request.remote_addr

        if len(extra) > 0:
            string += " - extra: " + str(extra)
        return string


def setup_logger():
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "class": "src.logging.ExFormatter",
                    "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": "INFO", "handlers": ["wsgi"]},
        }
    )

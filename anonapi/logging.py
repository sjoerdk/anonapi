"""Functions for writing messages to console in an organised way. logger.info()
worked well but there are too many layers and modules now to use only that
"""
import logging
from io import IOBase, UnsupportedOperation

import click


class ClickEchoIO(IOBase):
    """A stream that logger.info()'s each line that is written to it. Can be
    used ad stream for logging
    """

    def read(self):
        raise UnsupportedOperation("Cannot read, only print")

    @staticmethod
    def write(msg):
        click.echo(msg, nl=False)  # no newline, as this is already in msg


def configure_logging():
    """Route all log messages to click.echo(). Removes any other log handling"""
    click_stream = logging.StreamHandler(stream=ClickEchoIO())
    click_stream.setFormatter(logging.Formatter("%(name)s - %(levelname)s:%(message)s"))

    root = logging.getLogger()
    root.handlers = [click_stream]  # remove all other handlers
    root.setLevel(logging.DEBUG)

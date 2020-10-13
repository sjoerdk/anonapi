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


class AnonAPIFormatter(logging.Formatter):
    """A formatter with a single verbosity level to fit with cli -v or -vv..etc
    also, prints INFO message very plainly to not pollute regular output
    """

    TERSE = 1
    VERBOSE = 2
    ALL = [TERSE, VERBOSE]

    def __init__(self, verbosity: int = 1):
        super().__init__(self)
        self.verbosity = verbosity

    @staticmethod
    def format_record(record, pattern: str) -> str:
        return pattern.format(**vars(record))

    def format(self, record: logging.LogRecord) -> str:
        """Print INFO level messages plainly, rest with level name prepended"""
        if self.verbosity == self.TERSE:
            if record.levelno == logging.INFO:
                return self.format_record(record, "{msg}")
            else:
                return self.format_record(record, "{levelname}: {msg}")
        elif self.verbosity == self.VERBOSE:
            if record.levelno == logging.INFO:
                return self.format_record(record, "{name} - {msg}")
            else:
                return self.format_record(record, "{name} - {levelname}: {msg}")
        else:
            raise ValueError(
                f"Unknown verbosity level {self.verbosity}. " f"Allowed: {self.ALL}"
            )


def configure_logging():
    """Route all log messages to click.echo(). Removes any other log handling"""
    click_stream = logging.StreamHandler(stream=ClickEchoIO())
    click_stream.setFormatter(AnonAPIFormatter())

    root = logging.getLogger()
    root.handlers = [click_stream]  # remove all other handlers
    root.setLevel(logging.DEBUG)

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


class Verbosity(int):
    pass


class Verbosities:
    TERSE = Verbosity(1)
    VERBOSE = Verbosity(2)
    VERY_VERBOSE = Verbosity(3)
    ALL = [TERSE, VERBOSE, VERY_VERBOSE]


class AnonAPIFormatter(logging.Formatter):
    """A formatter with a single verbosity level to fit with cli -v or -vv..etc
    also, prints INFO message very plainly to not pollute regular output
    """

    def __init__(self, verbosity: Verbosity = Verbosities.TERSE):
        super().__init__()
        self.verbosity = verbosity

    @staticmethod
    def format_record(record, pattern: str) -> str:
        return pattern.format(**vars(record))

    def format(self, record: logging.LogRecord) -> str:
        """Print INFO level messages plainly, rest with level name prepended"""
        if self.verbosity == Verbosities.TERSE:
            if record.levelno == logging.INFO:
                return self.format_record(record, "{msg}")
            else:
                return self.format_record(record, "{levelname}: {msg}")
        elif self.verbosity == Verbosities.VERBOSE:
            if record.levelno == logging.INFO:
                return self.format_record(record, "{name} - {msg}")
            else:
                return self.format_record(record, "{name} - {levelname}: {msg}")
        else:
            raise ValueError(
                f"Unknown verbosity level {self.verbosity}. "
                f"Allowed:"
                f" {[Verbosities.TERSE, Verbosities.VERBOSE]}"
            )


class AnonAPILogController:
    """Holds on to a Logger instance and changes it according to a single verbosity
    scale.
    """

    def __init__(
        self, logger: logging.Logger, verbosity: Verbosity = Verbosities.TERSE
    ):
        """Set handler that prints to click.echo(). Removes any existing handlers"""
        self.logger = logger
        self.formatter = AnonAPIFormatter()

        click_stream = logging.StreamHandler(stream=ClickEchoIO())
        click_stream.setFormatter(self.formatter)

        self.logger.handlers = [click_stream]  # remove all other handlers
        self.set_verbosity(verbosity)

    def set_verbosity(self, verbosity: Verbosity):
        if verbosity == Verbosities.TERSE:
            self.formatter.verbosity = Verbosities.TERSE
            self.logger.setLevel(logging.INFO)

        elif verbosity == Verbosities.VERBOSE:
            self.formatter.verbosity = Verbosities.VERBOSE
            self.logger.setLevel(logging.INFO)

        elif verbosity == Verbosities.VERY_VERBOSE:
            self.formatter.verbosity = Verbosities.VERBOSE
            self.logger.setLevel(logging.DEBUG)

        else:
            raise ValueError(
                f"Unknown verbosity {verbosity}. " f"Allowed:{Verbosities.ALL}"
            )

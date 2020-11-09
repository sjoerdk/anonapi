"""Defines its own click method for testing logging, but tries to stay as close
to anonapi click methods as possible

Notes
-----
Testing log output depends on the tests.conftest.use_logging() fixture. Without
it most logs are not routed to click.echo
"""
import logging

import click

from anonapi.cli.entrypoint import cli
from anonapi.context import AnonAPIContext
from anonapi.logging import AnonAPILogController, Verbosities


@click.command(short_help="test logs")
@click.pass_obj
def logtest(context: AnonAPIContext):
    """A method that logs a lot"""
    logger_a = logging.getLogger("testloggerA")
    logger_b = logging.getLogger("testloggerB")

    logger_a.debug("some debug info")
    logger_a.info("some info")
    logger_a.warning("I'm warning you")
    logger_a.error("I told you!")
    logger_b.fatal("Oh the humanity!")


cli.add_command(logtest)


def test_logging(mock_main_runner):
    """Some assertions on what log messages should look like"""
    runner = mock_main_runner

    # overwrite log control from tests.conftest.use_logging()
    log_control = AnonAPILogController(
        logger=logging.getLogger(), verbosity=Verbosities.TERSE
    )

    # regular output should show loglevel, except for INFO, which should be concise
    assert_output(
        output=runner.invoke(logtest, catch_exceptions=False).output,
        expected="""some info
                    WARNING: I\'m warning you
                    ERROR: I told you!
                    CRITICAL: Oh the humanity!""",
    )

    # verbose output will add source of log message, but INFO still short
    log_control.set_verbosity(Verbosities.VERBOSE)

    assert_output(
        output=runner.invoke(logtest, catch_exceptions=False).output,
        expected="""testloggerA - some info
                    testloggerA - WARNING: I\'m warning you
                    testloggerA - ERROR: I told you!
                    testloggerB - CRITICAL: Oh the humanity!""",
    )

    # very verbose will also show debug messages
    log_control.set_verbosity(Verbosities.VERY_VERBOSE)

    assert_output(
        output=runner.invoke(logtest, catch_exceptions=False).output,
        expected="""testloggerA - DEBUG: some debug info
                    testloggerA - some info
                    testloggerA - WARNING: I\'m warning you
                    testloggerA - ERROR: I told you!
                    testloggerB - CRITICAL: Oh the humanity!""",
    )


def assert_output(output: str, expected: str):
    """Check whether multiline output is as expected. Assert line by line.
    Makes for more readable check and errors; if one line fails will yield
    assertion error for that line in particular

    Parameters
    ----------
    output: str
        multi-line click console output from calling logtest()
    expected:
    """
    for output, expected in zip(
        output.split("\n"), [x.lstrip() for x in expected.split("\n") if x]
    ):
        assert output == expected

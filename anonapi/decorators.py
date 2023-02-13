from functools import wraps

import click
from click.exceptions import ClickException

from anonapi.context import AnonAPIContext
from anonapi.batch import NoBatchDefinedError

# finds the nearest AnonAPIContext object and passes it to the wrapped click function
from anonapi.exceptions import AnonAPIError

pass_anonapi_context = click.make_pass_decorator(AnonAPIContext)


def handle_anonapi_exceptions(func):
    """Catch any AnonAPIExceptions and raise as ClickExceptions. This means no
    full stack trace for these errors. Hopefully a more user-friendly message

    Raises
    ------
    ClickException
        If any AnonAPIError occurs
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NoBatchDefinedError as e:
            raise ClickException(
                click.style(
                    f"No batch defined in current folder. You can create "
                    f"one with 'anon batch init'. Orignal error: '{e}'",
                    fg="red",
                )
            ) from e
        except AnonAPIError as e:
            raise ClickException(click.style(f"{e}", fg="red")) from e

    return wrapper

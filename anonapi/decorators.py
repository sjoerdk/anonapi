from functools import wraps

import click
from click.exceptions import ClickException

from anonapi.context import AnonAPIContext

# finds the nearest AnonAPIContext object and passes it to the wrapped click function
from anonapi.exceptions import AnonAPIException

pass_anonapi_context = click.make_pass_decorator(AnonAPIContext)


def handle_anonapi_exceptions(func):
    """Catch any AnonAPIExceptions and raise as ClickExceptions. This means no
    full stack trace for these errors. Hopefully a more user-friendly message

    Raises
    ------
    ClickException
        If any AnonAPIException occurs
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AnonAPIException as e:
            raise ClickException(click.style(f"{e}", fg="red"))

    return wrapper

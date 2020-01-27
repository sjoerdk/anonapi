import click

from anonapi.context import AnonAPIContext

# finds the nearest AnonAPIContext object and passes it to the wrapped click function
pass_anonapi_context = click.make_pass_decorator(AnonAPIContext)

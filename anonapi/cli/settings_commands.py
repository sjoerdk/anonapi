"""User sub commands

"""


import click

from anonapi.cli import user_commands


@click.group(name="settings")
def main():
    """manage local settings"""


main.add_command(user_commands.main)

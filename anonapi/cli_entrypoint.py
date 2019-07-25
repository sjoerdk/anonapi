"""Entrypoint for calling CLI with click. Split this off from code in cli module to isolate this module level
instantiation of several objects. This makes sure that importing cli does not do any hidden unwanted instantiations

"""
import pathlib

from anonapi.cli import AnonClientTool, AnonCommandLineParser
from anonapi.settings import AnonClientSettingsFromFile

settings_file = pathlib.Path.home() / "AnonWebAPIClientSettings.yml"
settings = AnonClientSettingsFromFile(settings_file)
tool = AnonClientTool(username=settings.user_name, token=settings.user_token)
parser = AnonCommandLineParser(client_tool=tool, settings=settings)
cli = parser.main

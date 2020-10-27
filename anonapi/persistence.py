"""Saving and loading things. Raising useful exceptions"""
import pathlib
from typing import Dict, TextIO

import yaml

from anonapi.exceptions import AnonAPIException


DEFAULT_SETTINGS_PATH = pathlib.Path.home() / "AnonWebAPIClientSettings.yml"


class YAMLSerializable:
    """A mixin for an object that can be saved to and loaded from yaml text.
    Requires implementation of to_dict() and from_dict() on the implementing object
    """

    def to_dict(self) -> dict:
        """Basis for json serialization. Overwrite this in child classes"""
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, dict_in: Dict) -> object:
        """Create object from dict. Basis for json serialization. Overwrite this in
        child classes to yield an instance of the the child class

        Raises
        ------
        ValueError
            If an object cannot be created from dict_in
        """
        raise NotImplementedError()

    @classmethod
    def load_from(cls, f: TextIO):
        """Load object from json stream

        Parameters
        ----------
        f: TextIO
            load object from this stream

        Raises
        ------
        PersistenceException
            If loading does not work

        Returns
        -------
        dict:
            The loaded json

        Raises
        ------
        PersistenceException
            When anything goes wrong during loading
        """
        content = yaml.safe_load(f)
        # check input here because exceptions later on will not be as informative
        if not isinstance(content, dict):
            raise PersistenceException(
                f"Loaded content is not a dictionary,"
                f" but rather {type(content)}. I can't "
                f"load this"
            )
        return cls.from_dict(content)

    def save_to(self, f: TextIO):
        """Save object to JSON stream

        Parameters
        ----------
        f: TextIO
            save object to this stream

        """
        yaml.dump(self.to_dict(), f, default_flow_style=False)


class PersistenceException(AnonAPIException):
    pass

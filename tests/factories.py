""" Shared classes used in other tests. For generating test data """
import itertools
from itertools import cycle
from pathlib import PureWindowsPath
from typing import List
from unittest.mock import Mock
from requests.models import Response
import factory

from anonapi.parameters import (
    PatientID,
    PatientName,
    Description,
    PIMSKey,
    SourceIdentifierParameter,
    FolderIdentifier,
    StudyInstanceUIDIdentifier,
    FileSelectionIdentifier,
    DestinationPath,
    RootSourcePath,
    Project,
)
from tests.mock_responses import RequestMockResponse


class PatientIDFactory(factory.Factory):
    class Meta:
        model = PatientID

    value = factory.sequence(lambda n: f"patientID{n}")


class PatientNameFactory(factory.Factory):
    class Meta:
        model = PatientName

    value = factory.sequence(lambda n: f"patientName{n}")


class ProjectFactory(factory.Factory):
    class Meta:
        model = Project

    value = factory.sequence(lambda n: f"project{n}")


class RootSourcePathFactory(factory.Factory):
    class Meta:
        model = RootSourcePath

    value = factory.sequence(
        lambda n: PureWindowsPath(f"\\\\server\\someshare\\folder{n}")
    )


class DescriptionFactory(factory.Factory):
    class Meta:
        model = Description

    value = factory.sequence(lambda n: f"A description, number {n}")


class DestinationPathFactory(factory.Factory):
    class Meta:
        model = DestinationPath

    value = factory.sequence(lambda n: f"/root_path{n}")


class PIMSKeyFactory(factory.Factory):
    class Meta:
        model = PIMSKey

    value = factory.sequence(lambda n: str(100 + n))


class FileSelectionIdentifierFactory(factory.Factory):
    class Meta:
        model = FileSelectionIdentifier

    identifier = factory.sequence(lambda n: f"folder/file{n}")


class FolderIdentifierFactory(factory.Factory):
    class Meta:
        model = FolderIdentifier

    identifier = factory.sequence(lambda n: f"folder{n}")


class StudyInstanceUIDIdentifierFactory(factory.Factory):
    class Meta:
        model = StudyInstanceUIDIdentifier

    identifier = factory.sequence(lambda n: f"123141513523{n}")


class SourceIdentifierIterator:
    classes = [
        FileSelectionIdentifierFactory,
        FolderIdentifierFactory,
        StudyInstanceUIDIdentifierFactory,
    ]

    def __iter__(self):
        self.class_iter = itertools.cycle(self.classes)
        return self

    def __next__(self):
        current_class = self.class_iter.__next__()
        return current_class()


class SourceIdentifierParameterFactory(factory.Factory):
    """Generates rows refer to sources. Uses different
    subclasses of SourceIdentifier as values

    """

    class Meta:
        model = SourceIdentifierParameter

    value = factory.Iterator(SourceIdentifierIterator())


class RequestsMock:
    """ Can be put in place of the requests module. Does not hit any server but
    returns kind of realistic arbitrary responses

    """

    def __init__(self):
        self.requests = Mock()  # for keeping track of past requests

    def set_response_text(self, text, status_code=200):
        """Any call to get() or post() will yield a Response() object with the given rows

        Parameters
        ----------
        text: str
            content to return
        status_code: int, optional
            http return code. Defaults to 200

        """
        response = self.create_response_object(status_code, text)

        self.requests.get.return_value = response
        self.requests.post.return_value = response

    @staticmethod
    def create_response_object(status_code, text):
        response = Response()
        response.encoding = "utf-8"
        response.status_code = status_code
        response._content = bytes(text, response.encoding)
        return response

    def set_response(self, response: RequestMockResponse):
        """Just for convenience"""
        self.set_responses([response])

    def set_responses(self, responses: List[RequestMockResponse]):
        """Any call to get() or post() will yield the given response. A list of responses will be looped over
        indefinitely

        Parameters
        ----------
        responses: List[RequestMockResponse]
            List of responses. Will be returned
        """

        objects = [
            self.create_response_object(response.response_code, response.text)
            for response in responses
        ]

        self.requests.get.side_effect = cycle(objects)
        self.requests.post.side_effect = cycle(objects)

    def set_response_exception(self, exception):
        """Any call to get() or post() will yield the given exception instance
        """
        self.requests.get.side_effect = exception
        self.requests.post.side_effect = exception

    def get(self, *args, **kwargs):
        return self.requests.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.requests.post(*args, **kwargs)

    def reset(self):
        self.requests.reset_mock()

    def called(self):
        """True if either get() or post() was called"""
        return self.requests.get.called or self.requests.post.called



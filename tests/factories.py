""" Shared classes used in other tests. For generating test data """

from unittest.mock import Mock
from requests.models import Response


class RequestsMock:
    """ Can be put in place of the requests module. Does not hit any server but returns kind of realistic arbitrary
    responses

    """
    def __init__(self):
        self.requests = Mock()  # for keeping track of past requests

    def set_response(self, text, status_code=200):
        """Any call to get() or post() will yield a Response() object with the given parameters

        Parameters
        ----------
        text: str
            content to return
        status_code: int, optional
            http return code. Defaults to 200

        """
        response = Response()
        response.encoding = 'utf-8'
        response.status_code = status_code
        response._content = bytes(text, response.encoding)

        self.requests.get.return_value = response
        self.requests.post.return_value = response

    def get(self, *args, **kwargs):
        return self.requests.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.requests.get(*args, **kwargs)

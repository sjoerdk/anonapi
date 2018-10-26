"""classes and methods shared by anonapi modules """


class RemoteAnonServer:
    """An anonymization server that can be talked to via the API

    """

    def __init__(self, name, url):
        """Create a Remote anon server entry

        Parameters
        ----------
        name: str
            short keyword to identify this server
        url: str
            full url to a valid Anonymization server web API
        """
        self.name = name
        self.url = url

    def __str__(self):
        return f"{self.name}: {self.url}"

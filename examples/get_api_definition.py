import pprint

from anonapi.client import WebAPIClient


def get_api_definition():
    """This function will print the API definition for the given hostname. Most readable way to do is just to load
    the API hostname (in this example https://umcradanonp11.umcn.nl/sandbox) in a web browser.

    """

    # Create a client that will talk to the web API
    client = WebAPIClient(
        hostname="https://umcradanonp11.umcn.nl/sandbox",
        username="z123sandbox",
        token="token",
    )

    documentation_dict = client.get_documentation()
    pp = pprint.PrettyPrinter(indent=2, compact=True)
    pp.pprint(documentation_dict)


if __name__ == "__main__":
    get_api_definition()

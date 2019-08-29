"""
Custom click parameter types
"""
import re

from click.types import ParamType

from anonapi.cli.parser import AnonCommandLineParser


class JobIDRangeParamType(ParamType):
    """A parameter that is either a single job ID "8" or a range of job ids "5-15".
    Will expand any range into a tuple min until max. Min and max inclusive

    """
    name = 'job_id'

    def convert(self, value, param, ctx):
        """If it looks like 'int-int' try to turn into range. Otherwise just leave as is and put in list

        Returns
        -------
        List[str]
            The value passed, or expanded range of ints represented by value passed

        """
        if value is None:
            return value

        if type(value) is list:
            return value  # Make sure function is idempotent. Feeding output into convert() again will not change output

        match = re.match('^(?P<start>[0-9]+)-(?P<end>[0-9]+)$', value)
        if match:  # expand range and add each item
            return [str(x) for x in range(int(match['start']), int(match['end']) + 1)]
        else:
            return [value]

    def __repr__(self):
        return 'JOB_ID_RANGE'


class AnonServerKeyParamType(ParamType):
    name = "anon_server_key"

    def convert(self, value, param, ctx):
        if not ctx:
            self.fail("This type expects an AnonCommandLineParser object in context")
        parser: AnonCommandLineParser = ctx.obj

        allowed = [x.name for x in parser.settings.servers]
        if value not in allowed:
            self.fail(f"'{value}' is not a registered anonymization server. Options: {allowed}")
        return value

    def __repr__(self):
        return 'ANON_SERVER_KEY'
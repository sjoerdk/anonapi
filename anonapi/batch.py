"""Work with batches of jobs
"""
import yaml

from anonapi.objects import RemoteAnonServer


class YamlSavable:

    def to_dict(self):
        """
        Returns
        -------
        Dict
        """
        raise NotImplemented()

    def save(self, f):
        """

        Parameters
        ----------
        f: FileHandle

        """
        yaml.dump(self.to_dict(), f, default_flow_style=False)

    @staticmethod
    def from_dict(dict_in):
        """

        Parameters
        ----------
        dict_in: Dict

        Returns
        -------
        Instance of this class

        """
        raise NotImplemented()

    @classmethod
    def load(cls, f):
        """Load an instance of this class

        Parameters
        ----------
        f: FileHandle

        Returns
        -------

        """
        flat_dict = yaml.safe_load(f)
        return cls.from_dict(dict_in=flat_dict)


class JobBatch(YamlSavable):
    """A collection of anonymisation jobs

    """

    def __init__(self, job_ids, server):
        """

        Parameters
        ----------
        job_ids: List(str)
            All job ids in this batch
        server: RemoteAnonServer
            Server these jobs were created in
        """
        self.job_ids = job_ids
        self.server = server

    def to_dict(self):
        """

        Returns
        -------
        str

        """
        return {'job_ids': self.job_ids,
                'server': self.server.to_dict()}

    @classmethod
    def from_dict(cls, dict_in):
        return cls(job_ids=dict_in['job_ids'], server=RemoteAnonServer.from_dict(dict_in['server']))





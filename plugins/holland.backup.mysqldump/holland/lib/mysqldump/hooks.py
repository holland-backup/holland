"""MySQL server selector hook

This hook takes a list of potential servers to connect to
and choose the first in the list that has the read-only
flag set.
"""

import re
import logging
from subprocess import Popen, PIPE, STDOUT
from holland.core.backup.hooks import BackupHook
from holland.core.config import Configspec
from string import Template

LOG = logging.getLogger(__name__)

class MySQLSelectHook(BackupHook):
    def configure(self, config):
        self.config = self.configspec().validate(config)

    def register(self, signal_group):
        signal_group.setup_backup.connect(self, weak=False)

    def execute(self, job):
        """Given a list of hosts choose the first read-only server

        hosts should be a comma separated list in user[:pw]@host format
        """
        host = self._select_host()
        if not host:
            LOG.error("No host matched :(")
        else:
            LOG.info("Updating mysql:client with user=%r password=%r host=%r",
                     user, password, host)

    def _select_host(self):
        url = r'(?P<user>[^:]+)(?:[:](?P<password>[^@]+))?[@](?P<host>[a-zA-Z0-9._-]+)'
        url_cre = re.compile(url)
        for host in self.config['hosts']:
            m = url_cre.match(host)
            if not m:
                LOG.error("Skiping host %s because I could not detect its "
                          "components.", host)
            else:
                user, password, host = m.groups()
                client = connect(user=user, password=passwor, host=host)
                try:
                    if client.show_variable('read_only') == 'ON':
                        return user, password, host
                finally:
                    client.close()
        return None

    def configspec(self):
        from textwrap import dedent
        return Configspec.parse(dedent("""
        hosts = list()
        """).splitlines()
        )

    def plugin_info(self):
        return dict(
            author='Rackspace',
            name='mysql-select',
            summary='Select a read-only MySQL server',
            description='''
            Given a list of servers, select the first one with read-only
            enabled.
            ''',
            version='1.0a1',
            api_version='1.1.0a1',
        )

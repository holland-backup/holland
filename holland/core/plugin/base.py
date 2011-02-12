"""Base plugin classes"""
import logging
from holland.core.config import Configspec, ValidateError

LOG = logging.getLogger(__name__)

class BasePlugin(object):
    """Base class from which all Holland plugins should derive"""
    #: name of this plugin
    name = None

    #: aliases for this plugin
    aliases = ()

    def __init__(self, name):
        self.name = name

    def plugin_info(self):
        """Provide information about this plugin

        :returns: Instance of ``PluginInfo``
        """
        raise NotImplementedError()

class ConfigurablePlugin(BasePlugin):
    """A plugin that accepts a configuration dictionary"""

    def configspec(self):
        """Provide a configspec that this plugin expects

        :returns: instance of holland.core.config.Configspec
        """
        return Configspec()

    def configure(self, config):
        """Configure this plugin with the given dict-like object"""
        try:
            self.config = self.configspec().validate(config)
        except ValidateError, exc:
            LOG.error("%d errors found while validating configuration",
                    len(exc.errors))
            for error in exc.errors:
                LOG.error("%s", error)
            raise

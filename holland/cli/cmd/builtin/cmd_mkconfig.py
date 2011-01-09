from holland.cli.cmd.base import ArgparseCommand, argument
#from holland.cli.config.util import cleanup_config

class MakeConfig(ArgparseCommand):
    name = 'mk-config'
    summary = "Generate a configuration file from a plugin"
    description = """
    Generate a configuration file from a plugin
    """

    arguments = [
        argument('--file'),
        argument('--name', help="Base name of the configuration to generate"),
        argument('--minimal', action='store_true'),
        argument('plugin-type')
    ]

    def execute(self, namespace):
        try:
            plugin = load_plugin('holland.backup', namespace.plugin_type)
        except PluginError, exc:
            self.error("Fail %s", exc)
            return 1

        configspec = plugin.configspec

        config = ConfigObj(base_config, configspec=configspec)
        check(config)       # validate, check for required keys
        cleanup(config)     # handle comments, comment out optional settings

        if namespace.edit:
            # allow edit
            # check(config); cleanup(config)
            # if failure, continue, else break
            while True:
                edit(config)
                try:
                    check(config)
                    cleanup(config)
                except Error:
                    if confirm("Errors were encountered. would you like to try again?"):
                       continue
                break

        output(config, namespace.file)

    #@classmethod
    def plugin_info(self):
        return PluginInfo(
            name=self.name,
            summary=self.summary,
            description=self.description,
            author='Rackspace',
            version='1.1.0',
            holland_version='1.1.0'
        )
    plugin_info = classmethod(plugin_info)

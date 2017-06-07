from holland.lib.configobj import ConfigObj
from holland.lib.validate import Validator
from checks import checks

from holland.helpers.log import get_logger, get_logging
from holland.helpers.providers import load_provider_resource, list_providers
import os
import pkg_resources as pkgr

config = ConfigObj()
spec = ConfigObj()

def extract_params(section):
    global config
    params = {}

    if section not in config:
        return params
    
    for option in config[section]:
        params[option] = config[section][option]

    return params

def get_config(**kwargs):
    global config
    global spec

    holland_conf = '/etc/holland/holland.conf'
    currplatform = sys.platform
    if currplatform.startswith('freebsd'):
        holland_conf = '/usr/local' + holland_conf

    config_file = os.path.abspath(kwargs.get("config_file",
                                             holland_conf))
    include_folders = kwargs.get("include_folders", ["providers",
                                                     "helpers",
                                                     "backupsets"])
    
    log = get_log(**kwargs)
    
    config_dir = os.path.join(*os.path.split(config_file)[:-1])
    log.debug("Detected configuration directory %s" % config_dir)
    
    log.debug("Getting initial config from %s" % config_file)
    config.merge(get_config_from_file(config_file))
    
    log.debug("Looking for config files")
    for folder in include_folders:
        folder_path = os.path.join(config_dir, folder)
        
        if not os.path.exists(folder_path):
            continue
        
        log.debug("Searching %s for config files" % folder_path)
        for included_config in get_configs_from_dir(dir=folder_path):
            log.debug("Merging %s into config" % included_config)
            config.merge(included_config)

    get_spec()

    log.debug("Reinitializing config with configspec")
    config = ConfigObj(config, configspec=spec)
    
    vtor = Validator()
    for check in checks:
        log.debug("Adding %s check to validator" % check)
        vtor.functions[check] = checks[check]
    
    log.debug("Validating config")
    errors = config.validate(vtor, preserve_errors=True)
    
    # Strip out unknown sections and keywords
    log.debug("Striping out unknown sections and keywords")
    known_sections = spec.keys()
    for section in config.keys():
        if section not in known_sections:
            log.warn("Section %s is not known, removing" % section)
            del config[section]
            continue
        for keyword,value in config[section].items():
            if isinstance(value, dict) and spec.get(section, {}).has_key('__many__'):
                continue
            if keyword not in spec.get(section, {}).keys():
                log.warn("Keyword %s in section %s is not known, removing" % \
                         (keyword, section))
                del config[section][keyword]
    log.debug("Going forth with config: %s" % config)


def get_configs_from_dir(dir):
    configs = []
    log = get_log()
    
    for root, dirs, files in os.walk(os.path.abspath(dir)):
        for config_file in files:
            config_file = os.path.join(root, config_file)
            log.debug("Found file %s" % config_file)
            configs.append(get_config_from_file(config_file))
    return configs

def get_config_from_file(file):
    return ConfigObj(file)

def get_spec():
    global spec
    log = get_log()

    log.debug("Looking for configspecs")
    for file_spec in pkgr.resource_listdir("holland", "validators"):
        if file_spec.endswith("configspec"):
            log.debug("Found configspec %s" % file_spec)
            file_stream = pkgr.resource_stream("holland",
                                               "validators/" + file_spec)
            log.debug("Merging %s into spec" % file_spec)
            spec.merge(ConfigObj(file_stream,list_values=False))
    
    log.debug("Searching providers for configspecs")
    for provider_spec in get_specs_from_providers():
        spec.merge(provider_spec)

def get_specs_from_providers():
    specs = []
    log = get_log()
    
    providers = list_providers()
    for provider in providers.keys():
        log.debug("Looking for configspec from %s" % providers[provider][0])
        provider_spec = get_provider_spec(providers[provider][0])
        specs.append(ConfigObj(provider_spec,list_values=False))
        
    return specs

def get_connect_params(**kwargs):
    # generate dictionary of params to pass to MySQLdb connect
    section = kwargs.get("section", "mysql_connect")
    return extract_params(section)

def setup_bootstrap_logging(**kwargs):
    # When we first startup logging needs the config, but the config needs
    # logging.  This will setup enough of logging to log the config parsing.
    # No validation or checking is preformed, we just need a log file to
    # write to.

    holland_conf = '/etc/holland/holland.conf'
    currplatform = sys.platform
    if currplatform.startswith('freebsd'):
        holland_conf = '/usr/local' + holland_conf

    config_file = kwargs.get("config_file", holland_conf)
    
    log_config = ConfigObj(os.path.abspath(config_file), file_error=True)
    log_file = log_config["logging"]["log_filename"]
    
    logging = get_logging()
    log = logging.getLogger("holland")
    
    log.setLevel(logging.DEBUG)
    
    bootstrap_logging = logging.FileHandler(log_file)
    bootstrap_logging.name = "bootstrap"
    bootstrap_logging.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
                            "%(asctime)s %(name)s %(levelname)s: %(message)s")
    
    bootstrap_logging.setFormatter(formatter)
    log.addHandler(bootstrap_logging)

    
def get_log(**kwargs):
    log = get_logger("holland")

    if len(log.handlers) == 0:
        setup_bootstrap_logging(**kwargs)

    return get_logger(__name__)

def get_log_config(**kwargs):
    # generate dictionary of params to pass to setup_logger
    global config
    section = kwargs.get("section", "logging")
    force_verbose = kwargs.get("stdout_verbose", False)
    
    if not config:
        get_config(**kwargs)
        
    params = extract_params(section)
    
    if force_verbose and params.has_key("stdout_verbose"):
        if not params["stdout_verbose"]:
            params["stdout_verbose"] = force_verbose

    return params

def get_provider_spec(provider_name):
    """
    Find the configspec from the provider
    This will throw a LookupError if no configspec is found, or the 
    provider does not exist
    """
    cfgspec = load_provider_resource(provider_name, 
                                    'validators/%s.configspec' % provider_name)
    return cfgspec.strip().splitlines()    

def rel_path(base, target):
    path = []
    dir, file = os.path.split(os.path.abspath(target))
    path.append(file)
    while dir != os.path.abspath(base):
        dir, file = os.path.split(dir)
        path.append(file)
    path.reverse()
    return os.path.join(*path)

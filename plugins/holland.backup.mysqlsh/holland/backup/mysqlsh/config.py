"""
Common configuration options for mysqlsh backup plugins
"""

from itertools import chain

from holland.lib.mysql.client.base import MYSQL_CLIENT_CONFIG_STRING

BASE_OPTIONS = {
    "executable": {"type": "string", "default": "mysqlsh"},
    "bin-log-position": {"type": "boolean", "default": False},
    "estimate-method": {"type": "string", "default": "plugin"},
    "extra-defaults": {"type": "boolean", "default": False},
    "log-level": {"type": "string", "default": "5"},
    "stop-slave": {"type": "boolean", "default": False},
    "additional-options": {"type": "force_list", "default": []},
}

MYSQLSH_SHARED_OPTIONS = {
    "threads": {"type": "integer", "default": 4},
    "max-rate": {"type": "string", "default": "0"},
    "consistent": {"type": "boolean", "default": True},
    "skip-consistency-checks": {"type": "boolean", "default": False},
    "tz-utc": {"type": "boolean", "default": True},
    "compression": {"type": "string", "default": "zstd"},
    "chunking": {"type": "boolean", "default": True},
    "bytes-per-chunk": {"type": "string", "default": "64M"},
    "ddl-only": {"type": "boolean", "default": False},
    "data-only": {"type": "boolean", "default": False},
    "exclude-tables": {"type": "force_list", "default": []},
    "include-tables": {"type": "force_list", "default": []},
    "events": {"type": "boolean", "default": True},
    "exclude-events": {"type": "force_list", "default": []},
    "include-events": {"type": "force_list", "default": []},
    "routines": {"type": "boolean", "default": True},
    "exclude-routines": {"type": "force_list", "default": []},
    "include-routines": {"type": "force_list", "default": []},
    "triggers": {"type": "boolean", "default": True},
    "exclude-triggers": {"type": "force_list", "default": []},
    "include-triggers": {"type": "force_list", "default": []},
    "strip-definers": {"type": "boolean", "default": False},
    "create-invisible-pks": {"type": "boolean", "default": False},
}


def generate_configspec(config_key, plugin_options=None):
    """Generate the CONFIGSPEC string from both Holland and mysqlsh options."""
    configspec = [f"[{config_key}]"]

    # Add Holland-specific options
    for opt_name, metadata in chain(
        BASE_OPTIONS.items(),
        MYSQLSH_SHARED_OPTIONS.items(),
        (plugin_options or {}).items(),
    ):
        if metadata["type"] == "option":
            options_str = ", ".join(f"'{opt}'" for opt in metadata["options"])
            configspec.append(
                f"{opt_name} = option({options_str}, default={metadata.get('default')})"
            )
        elif metadata["type"] == "force_list":
            if not metadata["default"]:
                default = "list()"
            else:
                default = "list(" + ", ".join(metadata["default"]) + ")"
            configspec.append(f"{opt_name} = force_list(default={default})")
        else:
            configspec.append(
                f"{opt_name} = {metadata['type']}(default={metadata['default']})"
            )
    # Add MySQL client configuration
    configspec.extend(MYSQL_CLIENT_CONFIG_STRING.splitlines())

    return configspec

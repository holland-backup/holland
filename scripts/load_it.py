import os
from holland.core.plugin import add_plugin_dir, get_distribution
import logging

logging.basicConfig(level=logging.DEBUG)

logging.info(logging)

path = os.path.abspath('env/usr/share/holland/plugins')
add_plugin_dir(path)

dist = get_distribution("holland.plugin.mysqldump")

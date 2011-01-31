"""Backup plugin template for paster"""

from paste.script.templates import Template, var
from holland import __version__ as holland_version

vars = [
    var('version', 'Version (like 0.1)'),
    var('description', 'One-line description of the package'),
    var('long_description', 'Multi-line description (in reST)'),
    var('keywords', 'Space-separated keywords/tags'),
    var('author', 'Author name'),
    var('author_email', 'Author email'),
    var('url', 'URL of homepage'),
    var('license_name', 'License name'),
    var('plugin', 'Name of the holland plugin'),
    var('plugin_version', 'Plugin Version (like 0.1)'),
    var('plugin_summary', 'One-line description of plugin'),
    var("plugin_description", "Multi-line description"),
    var('api_version',
        "Version of holland this plugin will be written against",
        default=holland_version),
]

class HollandBackupTemplate(Template):
    """Holland Backup Plugin template for paster"""
    _template_dir = 'templates/backup'
    summary = 'Holland Backup Template'
    required_templates = ['basic_package']
    vars = vars

    def post(self, command, output_dir, vars):
        import os, shutil
        path = os.path.join(output_dir, vars['package'])
        shutil.rmtree(path)

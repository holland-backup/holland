Holland CLI Internals Documentation
===================================

This page attempts to document the internal implementation of ``holland.cli`` -
the command line frontend to Holland.

``/usr/sbin/holland`` script
----------------------------
The primary ``holland`` command starts in ``holland.cli.main``.  This performs
the basic configuration of the frontend from holland.conf and initializes the
runtime environment from that config (logging, umask, tmpdir, etc.).

.. autoclass:: holland.cli.main.HollandCli
   :members:

``holland`` dispatches to various subcommands looked up through the
``holland.cli`` command API.  This is done through
``holland.cli.cmd.BaseCommand.chain()``.  See the command API for more
information.

Logging
-------

``HollandCli`` uses the stdlib ``logging`` module to configure both a file and
console logger.  This is configured in ``holland.cli.log.configure_logging()``

.. autofunction:: holland.cli.log.configure_logging

``configure_logging()`` will also trap messages from the stdlib ``warnings`` 
module.  This is mean to only log those warning messages in debug mode and
avoid writing distracting messages to an end user.  Currently this only
traps ``DeprecationWarnings``

.. autofunction:: holland.cli.log.configure_warnings

.. autofunction:: holland.cli.log.log_warning

Backports
---------
``holland.cli.backports`` provide several modules from recent python versions
backported for older python releases.  These are designed to work on python2.3+
and include the following stdlib packages:

  * subprocess.py - Backported from python2.7; Used by many holland plugins
  * argparse.py   - Backported from python2.7; Used by the cli

The holland cli will automatically add these to sys.path to avoid any special
behavior on the part of plugins to support these modules for older python
releases.

Command API
-----------

``holland.cli`` provides a pluggable command api that allows external
commands to be added by external providers.

.. automodule:: holland.cli.cmd
   :members:

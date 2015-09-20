.. _config-rsync:

rsync
=====

Uses ``rsync`` to backup a local or remote directory, optionally by making use of
hardlinks as a means to provide a sort of differential backup.

Configuration
-------------

[rsync]
_______

**method** = local | rsync | ssh (default: local)

    Method to sync with which can be local (for a local directory copy),
    ssh for using secure shell, or rsync for using the rsync protocol.

**server** = <hostname or IP address> (default: none)

    If performing a backup of a remote directory, which server to
    pull the content from.

**port** = <TCP port> (default: none)

    An optional setting to specify a custom port to connect to when using the
    rsync or SSH methods.

**username** = <username> (default: none)

    An optional setting to specify a username to connect with when using the
    rsync or SSH methods.

**keyfile** = <path> (default: none)

    An optional setting to specify an SSH keyfile to use with the SSH method.
    This should be an absolute path. Be sure to escape spaces.
    (e.g. ``/directory/with\ spaces``)

**password** = <cleartext password> (default: none)

    An option setting to specify an rsync password to use with the rsync method.
    This password is in cleartext so be sure to make the appropriate security
    precautions.

**directory** = <path> (default: /)

    The path of the source directory to backup from. Be sure to escape spaces.
    (e.g. ``/directory/with\ spaces``)

**flags** = <rsync short-flags> (default: -av)

    The short-flags to pass to rsync. See the rsync manpage for a full listing,
    though for the most part, ``-av`` works well for local backups and ``-avz``
    for remote backups (``z`` being for compression to save on bandwidth).

**hardlinks** = <yes | no> (default: yes)

    Whether or not to create hardlinks from the previous backup if a file has
    not been changed. This facilitates a kind of differential backup which,
    as long as the destination is considered reliable, can save lots of space
    when opting to keep more than one backup.

**one-file-system** = <yes | no> (default: no)

    Whether or not to cross file-systems during the backup. This is often
    useful for avoiding additional mountpoints without having to use the
    exclusions list. A common case where this is useful is when backing up /,
    as this setting would cause /proc, /sys and any mounted disks to be skipped.

**bandwidth-limit** = <size with units> (default: none)

    To keep rsync from taking up a lot of bandwidth and/or disk I/O, speocify
    a maximum transfer-rate, specified in units per second. (e.g. "2MB").
    See the --max-size and --bwlimit sections of the rsync manpage for more
    information.

**exclude** = <comma seperated list> (default: none)

    A list (actually a tuple in Python-speak) of exclusions. These are files or
    directories to use in one or more --exclude flags passed to rsync.
    e.g. ``file1,file2,...``

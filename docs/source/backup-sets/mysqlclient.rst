[mysql:client]
**************

**defaults-extra-file** = path to include, or None

    Specify a defaults file to pass to MySQL. This is typically used to i
    pull in login information (say from ~/.my.cnf).

**user** = username or None

    Specify a username. If empty, Holland will use the defaults file (if
    defined), or whatever is configured in the enviornment variables
    or what MySQL uses by default.

**password** = password or None

    Specify a password (cleartext). If empty, Holland will use the defaults 
    file (if defined), or whatever is configured in the enviornment variables
    or what MySQL uses by default.

**socket** = socket or None

    Specify a socket file. If empty, Holland will use the defaults file (if
    defined), or whatever is configured in the enviornment variables or what 
    MySQL uses by default.

**host** = hostname or None

    Specify a hostname or IP address. If empty, Holland will use the 
    defaults file (if defined), or whatever is configured in the enviornment 
    variables or what MySQL uses by default.

**port** = # or None

    Specify a port. If empty, Holland will use the defaults file (if
    defined), or whatever is configured in the enviornment variables or what 
    MySQL uses by default.

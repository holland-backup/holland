"""Config utility methods"""

import re

def unquote(value):
    """Remove quotes from a string

    This will both remove quotes at the start
    and end of a string and substitute any escaped
    characters with their real values.
    """
    escape_cre = re.compile(r'''\\(['"t\\])''')
    substitutions = {
        't' : "\t",
        '\\': "\\",
        '"' : '"',
        "'" : "'",
    }
    if len(value) and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    elif len(value) > 1 and value[0] == "'" and value[-1] == "'":
        value = value[1:-1]

    return escape_cre.sub(lambda m: substitutions[m.group(1)], value)

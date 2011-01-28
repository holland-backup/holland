import re

def unquote(value):
    """Remove quotes from a string."""
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

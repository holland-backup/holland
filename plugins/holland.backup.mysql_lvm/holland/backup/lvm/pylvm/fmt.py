"""LVM formatting and validation methods"""

import re
from math import log

def format_size(bytes, precision=4):
    """
    Format an integer number of bytes to a human
    readable string.

    """
    units = "KMGTPE"

    if bytes < 1024:
        raise ValueError("LVM does not support units lower than 1K")

    exponent = int(log(abs(bytes), 1024))

    # Offset into our units sequence
    # min = 0, max = 5 (E => exabytes)
    unit_index = min(max(exponent - 1, 0), len(units) - 1)

    # limit exponent for very large units
    exponent = min(exponent, len(units))

    return "%.*f%s" % (
        precision,
        bytes / (1024.0 ** exponent),
        units[unit_index]
    )

def parse_size(units_string):
    """Parse an LVM size string into bytes"""

    units_string = str(units_string)

    units = "kKmMgGtTpPeE"

    match = re.match(r'^(\d+(?:[.]\d+)?)([%s]|)$' % units, units_string)
    if not match:
        raise ValueError("Invalid LVM Unit syntax %r" % units_string)
    number, unit = match.groups()
    if not unit:
        unit = 'M'
    unit = unit.upper()

    exponent = "KMGTPE".find(unit)

    return int(float(number) * 1024 ** (exponent + 1))

def validate_size(units_string):
    """Validate an LVM size specification"""
    return format_size(parse_size(units_string))

def validate_name(lv_or_vg_name):
    """Validate an LVM object name according the spec from lvm(8)"""
    # ., .. are prohibited for VG
    # additionally, LV also cannot be named snapshot or pvmove
    prohibited_names = ('.', '..', 'snapshot', 'pvmove')
    # These only apply to LVs and may not appear anywhere in the name
    prohibited_patterns = ('_mlog', '_mimage')
    namecre = re.compile(r'^[a-zA-Z0-9+_.][a-zA-Z0-9+_.-]*$')
    for name in prohibited_names:
        if name == lv_or_vg_name:
            raise ValueError("Invalid name %r" % lv_or_vg_name)
    for pat in prohibited_patterns:
        if pat in lv_or_vg_name:
            raise ValueError("LV may not contain %r" % pat)

    if namecre.match(lv_or_vg_name) is None:
        # This is really a lexical error, right?
        raise ValueError("Invalid name %r" % lv_or_vg_name)

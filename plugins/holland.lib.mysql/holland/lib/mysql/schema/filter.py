"""Simple Filter support"""

import re
import fnmatch

class BaseFilter(object):
    """Filter a string based on a list of regular expression or glob patterns.

    This should be inherited and the __call__ overriden with a real
    implementation
    """
    __slots__ = ('patterns', '_re_options')

    def __init__(self, patterns, case_insensitive=True):
        self.patterns = list(patterns)
        if case_insensitive:
            self._re_options = re.M|re.U|re.I
        else:
            self._re_options = re.M|re.U

    def add_glob(self, glob):
        """Add a glob pattern to this filter

        Internally all globs are converted to regular expressions using
        `fnmatch.translate()`

        :param glob: glob pattern to add
        :type glob: str
        """
        self.patterns.append(fnmatch.translate(glob))

    def add_regex(self, regex):
        """Add a regular expression pattern to this filter

        :param regex: regular expression pattern to add to this filter.
        :type regex: str
        """
        self.patterns.append(regex)

    def __call__(self, item):
        """Run this filter - return True if filtered and False otherwise.

        :param item: item to check against this filter
        :type item: str
        """
        raise NotImplementedError()

class IncludeFilter(BaseFilter):
    """Include only objects that match *all* assigned filters"""

    def __call__(self, item):
        for _pattern in self.patterns:
            if re.match(_pattern, item, self._re_options) is not None:
                return False
        else:
            return True

class ExcludeFilter(BaseFilter):
    """Exclude objects that match any filter"""

    def __call__(self, item):
        for _pattern in self.patterns:
            if re.match(_pattern, item, self._re_options) is not None:
                return True
        else:
            return False

def exclude_glob(*pattern):
    """Create an exclusion filter from a glob pattern"""
    return ExcludeFilter([fnmatch.translate(pat) for pat in pattern])

def include_glob(*pattern):
    """Create an inclusion filter from glob patterns"""
    return IncludeFilter([fnmatch.translate(pat) for pat in pattern])

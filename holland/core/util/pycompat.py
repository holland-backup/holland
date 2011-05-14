"""
    holland.core.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Methods and classes backported from more recent versions of python to
    provide support for older python versions

    Presently this module should be compatible back to python2.3

    Two components are currently backported here:
        * re.Scanner from python2.6 - useful for regex based tokenizers
        * string.Template from python2.4 - simple string interpolation

    :license: PSF, see LICENSE.rst for details
"""


import re
import textwrap
from keyword import iskeyword
try:
    set
except NameError:
    from sets import Set as set

class Scanner(object):
    """A simple regular expression based scanner

    This class can be used to tokenize a string based on a series of regular
    expression rules.
    """
    def __init__(self, lexicon, flags=0):
        import sre_parse
        import sre_compile
        from sre_constants import BRANCH, SUBPATTERN
        self.lexicon = lexicon
        # combine phrases into a compound pattern
        p = []
        s = sre_parse.Pattern()
        s.flags = flags
        for phrase, action in lexicon:
            p.append(sre_parse.SubPattern(s, [
                (SUBPATTERN, (len(p)+1, sre_parse.parse(phrase, flags))),
                ]))
        s.groups = len(p)+1
        p = sre_parse.SubPattern(s, [(BRANCH, (None, p))])
        self.scanner = sre_compile.compile(p)

    def scan(self, string):
        """Scan string and return a list of tokens

        :returns: 2-tuple: list of tokens, str of remainder of string that
                  could not be scanned
        """
        result = []
        append = result.append
        match = self.scanner.scanner(string).match
        i = 0
        while 1:
            m = match()
            if not m:
                break
            j = m.end()
            if i == j:
                break
            action = self.lexicon[m.lastindex-1][1]
            if hasattr(action, '__call__'):
                self.match = m
                action = action(self, m.group())
            if action is not None:
                append(action)
            i = j
        return result, string[i:]

class _TemplateMetaclass(type):
    pattern = r"""
    %(delim)s(?:
      (?P<escaped>%(delim)s) |   # Escape sequence of two delimiters
      (?P<named>%(id)s)      |   # delimiter and a Python identifier
      {(?P<braced>%(id)s)}   |   # delimiter and a braced identifier
      (?P<invalid>)              # Other ill-formed delimiter exprs
    )
    """

    def __init__(cls, name, bases, dct):
        super(_TemplateMetaclass, cls).__init__(name, bases, dct)
        if 'pattern' in dct:
            pattern = cls.pattern
        else:
            pattern = _TemplateMetaclass.pattern % {
                'delim' : re.escape(cls.delimiter),
                'id'    : cls.idpattern,
                }
        cls.pattern = re.compile(pattern, re.IGNORECASE | re.VERBOSE)


class Template(object):
    """A string class for supporting $-substitutions."""
    __metaclass__ = _TemplateMetaclass

    delimiter = '$'
    idpattern = r'[_a-z][_a-z0-9]*'

    def __init__(self, template):
        self.template = template

    # Search for $$, $identifier, ${identifier}, and any bare $'s

    def _invalid(self, mo):
        i = mo.start('invalid')
        lines = self.template[:i].splitlines(True)
        if not lines:
            colno = 1
            lineno = 1
        else:
            colno = i - len(''.join(lines[:-1]))
            lineno = len(lines)
        raise ValueError('Invalid placeholder in string: line %d, col %d' %
                         (lineno, colno))

    def substitute(self, *args, **kws):
        from datastructures import MergeDict as _multimap
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _multimap(kws, args[0])
        else:
            mapping = args[0]
        # Helper function for .sub()
        def convert(mo):
            # Check the most common path first.
            named = mo.group('named') or mo.group('braced')
            if named is not None:
                val = mapping[named]
                # We use this idiom instead of str() because the latter will
                # fail if val is a Unicode containing non-ASCII characters.
                return '%s' % (val,)
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                self._invalid(mo)
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)

    def safe_substitute(self, *args, **kws):
        from datastructures import MergeDict as _multimap
        if len(args) > 1:
            raise TypeError('Too many positional arguments')
        if not args:
            mapping = kws
        elif kws:
            mapping = _multimap(kws, args[0])
        else:
            mapping = args[0]
        # Helper function for .sub()
        def convert(mo):
            named = mo.group('named')
            if named is not None:
                try:
                    # We use this idiom instead of str() because the latter
                    # will fail if val is a Unicode containing non-ASCII
                    return '%s' % (mapping[named],)
                except KeyError:
                    return self.delimiter + named
            braced = mo.group('braced')
            if braced is not None:
                try:
                    return '%s' % (mapping[braced],)
                except KeyError:
                    return self.delimiter + '{' + braced + '}'
            if mo.group('escaped') is not None:
                return self.delimiter
            if mo.group('invalid') is not None:
                return self.delimiter
            raise ValueError('Unrecognized named group in pattern',
                             self.pattern)
        return self.pattern.sub(convert, self.template)


def namedtuple(typename, field_names, verbose=False, rename=False, doc=None):
    """
    Returns a :class:`tuple` subclass named `typename` with a limited number
    of possible items who are accessible under their field name respectively.

    Due to the implementation `typename` as well as all `field_names` have to
    be valid python identifiers also the names used in `field_names` may not
    repeat themselves.

    You can solve the latter issue for `field_names` by passing ``rename=True``,
    any given name which is either a keyword or a repetition is then replaced
    with `_n` where `n` is an integer increasing with every rename starting by
    1.

    :func:`namedtuple` creates the code for the subclass and executes it
    internally you can view that code by passing ``verbose==True``, which will
    print the code.

    Unlike :class:`tuple` a named tuple provides several methods as helpers:

    .. class:: SomeNamedTuple(foo, bar)

       .. classmethod:: _make(iterable)

          Returns a :class:`SomeNamedTuple` populated with the items from the
          given `iterable`.

       .. method:: _asdict()

          Returns a :class:`dict` mapping the field names to their values.

       .. method:: _replace(**kwargs)

          Returns a :class:`SomeNamedTuple` values replaced with the given
          ones::

              >>> t = SomeNamedTuple(1, 2)
              >>> t._replace(bar=3)
              SomeNamedTuple(foo=1, bar=3)
              # doctest: DEACTIVATE

    .. note::
       :func:`namedtuple` is compatible with :func:`collections.namedtuple`.

    .. versionadded:: 0.5
    """
    def name_generator():
        for i in count(1):
            yield '_%d' % i
    make_name = name_generator().next

    if iskeyword(typename):
        raise ValueError('the given typename is a keyword: %s' % typename)
    if isinstance(field_names, basestring):
        field_names = field_names.replace(',', ' ').split()
    real_field_names = []
    seen_names = set()
    for name in field_names:
        if iskeyword(name):
            if rename:
                name = make_name()
            else:
                raise ValueError('a given field name is a keyword: %s' % name)
        elif name in seen_names:
            if rename:
                name = make_name()
            else:
                raise ValueError('a field name has been repeated: %s' % name)
        real_field_names.append(name)
        seen_names.add(name)

    code = textwrap.dedent("""
        try:
            from operator import itemgetter
        except ImportError:
            def itemgetter(*items):
                '''Return a callable object that fetches item from its operand using
                 the operand's __getitem__() method.
                '''
                if len(items) == 1:
                    item = items[0]
                    def g(obj):
                        return obj[item]
                else:
                    def g(obj):
                        return tuple([obj[item] for item in items])
                return g

        class %(typename)s(tuple):
            '''%(docstring)s'''

            _fields = %(fields)s

            #@classmethod
            def _make(cls, iterable):
                result = tuple.__new__(cls, iterable)
                if len(result) > %(field_count)d:
                    raise TypeError(
                        'expected %(field_count)d arguments, got %%d' %% len(result)
                    )
                return result
            _make = classmethod(_make)

            def __new__(cls, %(fieldnames)s):
                return tuple.__new__(cls, (%(fieldnames)s))

            def _asdict(self):
                return dict(zip(self._fields, self))

            def _replace(self, **kwargs):
                result = self._make(map(kwargs.pop, %(fields)s, self))
                if kwargs:
                    raise ValueError(
                        'got unexpected arguments: %%r' %% kwargs.keys()
                    )
                return result

            def __getnewargs__(self):
                return tuple(self)

            def __repr__(self):
                return '%(typename)s(%(reprtext)s)' %% self
    """) % {
        'typename': typename,
        'fields': repr(tuple(real_field_names)),
        'fieldnames': ', '.join(real_field_names),
        'field_count': len(real_field_names),
        'reprtext': ', '.join([name + '=%r' for name in real_field_names]),
        'docstring': doc or typename + '(%s)' % ', '.join(real_field_names)
    }

    for i, name in enumerate(real_field_names):
        code += '    %s = property(itemgetter(%d))\n' % (name, i)

    if verbose:
        print code

    namespace = {}
    # there should never occur an exception here but if one does I'd rather
    # have the source to see what is going on
    try:
        exec code in namespace
    except SyntaxError, e: # pragma: no cover
        raise SyntaxError(e.args[0] + ':\n' + code)
    result = namespace[typename]

    return result

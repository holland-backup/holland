"""Parse configspec checks"""

import re
from holland.core.config.util import unquote, missing
try:
    Scanner = re.Scanner
except AttributeError:
    from holland.core.util.pycompat import Scanner

__all__ = [
    'Check',
    'CheckError',
]

class Token(object):
    """Lexer token"""
    def __init__(self, text, token_id, value, position=()):
        self.text = text
        self.id = token_id
        self.value = value
        self.position = position

    def __repr__(self):
        position = map(str, self.position)
        return 'Token(text=%r, type=%r, value=%r, position=%r)' % \
                (self.text, self.id, self.value, '-'.join(position))


class TokenGenerator(object):
    """Generate a token"""
    def __init__(self, token_id, conversion=str):
        self.token_id = token_id
        self.conversion = conversion

    def __call__(self, scanner, value):
        return Token(text=value,
                     token_id=self.token_id,
                     value=self.conversion(value),
                     position=scanner.match.span())


class Lexer(object):
    """Simple lexer of an iterable of tokens"""
    def __init__(self, iterable):
        self.iterable = iter(iterable)

    def expect(self, *token_ids):
        """Fetch the next token and raise a CheckParseError if its
        type is not one of the provided, expected token ids

        :returns: next Token instance
        """
        token = self.next()
        if token.id not in token_ids:
            raise CheckParseError("Expected one of %r but got %r" %
                             (token_ids, token))
        return token

    def next(self):
        """Fetch the next token

        :returns: Token instance
        """
        try:
            tok = self.iterable.next()
            return tok
        except StopIteration:
            raise CheckParseError("Reached end-of-input when reading token")

    def __iter__(self):
        return self

class CheckError(Exception):
    """Raise when an error is occured during a check"""

class CheckParseError(Exception):
    """Raised when an error is encountered during parsing a check string"""


class CheckParser(object):
    """Parse the check DSL supported by ``Configspec``"""
    T_ID        = 1
    T_STR       = 2
    T_NUM       = 4
    T_SYM       = 16

    # rule patterns
    ident_re    = r'[a-zA-Z_][a-zA-Z0-9_]*'
    name_re     = r'[a-zA-Z_-][a-zA-Z0-9_-]*'
    str_re      = (r"'([^'\\]*(?:\\.[^'\\]*)*)'"r'|"([^"\\]*(?:\\.[^"\\]*)*)"')
    float_re    = r'(?<!\.)\d+\.\d+'
    int_re      = r'\d+'
    sym_re      = r'[()=,]'
    space_re    = r'\s+'

    # scanner
    scanner = Scanner([
        (ident_re, TokenGenerator(T_ID)),
        (str_re, TokenGenerator(T_STR, unquote)),
        (float_re, TokenGenerator(T_NUM, float)),
        (int_re, TokenGenerator(T_NUM, int)),
        (sym_re, TokenGenerator(T_SYM)),
        (space_re, None)
    ])

    #@classmethod
    def parse(cls, check):
        """Parse a check

        This is primarily used implicitly by ``Configspec`` to lookup checks by name
        in its own registry.

        :returns: tuple (check_name, args, kwargs)
        """
        tokens, remainder = cls.scanner.scan(check)

        if remainder:
            offset = len(check) - len(remainder)
            raise CheckParseError("Unexpected character at offset %d\n%s\n%s" %
                                  (offset, check, " "*offset + "^"))

        lexer = Lexer(tokens)

        method = lexer.next()
        if method.id != cls.T_ID:
            raise CheckParseError("Expected identifier as first token in check "
                             "string but got %r" % method.id)

        # bare-name check
        try:
            token = lexer.next()
        except CheckParseError:
            return method.value, (), {}

        if token.text != '(':
            raise CheckParseError("Expected '(' as token following method name")

        args, kwargs = cls._parse_argument_list(lexer)

        return method.value, args, kwargs
    parse = classmethod(parse)

    #@classmethod
    def _parse_argument_list(cls, lexer):
        args = []
        kwargs = {}
        for token in lexer:
            if token.text == ')':
                break
            if token.id not in (cls.T_ID, cls.T_STR, cls.T_NUM):
                raise CheckParseError("Unexpected token %r" % token)

            arg = cls._parse_expression(lexer, token)
            token = lexer.expect(cls.T_SYM)
            if token.text == '=':
                value = cls._parse_expression(lexer, lexer.next())
                kwargs[arg] = value
                token = lexer.next()
            else:
                args.append(arg)

            if token.text != ',':
                break

        if token.text != ')':
            raise CheckParseError("Expected check expression to end with ')' "
                             "but got %r" % token)
        return tuple(args), kwargs
    _parse_argument_list = classmethod(_parse_argument_list)

    #@classmethod
    def _parse_expression(cls, lexer, token):
        if token.id in (cls.T_STR, cls.T_NUM):
            # literal value
            return token.value
        elif token.id == cls.T_ID and token.text != 'list':
            if token.text == 'None':
                return None
            return token.value
        else:
            return cls._parse_list_expr(lexer)
    _parse_expression = classmethod(_parse_expression)

    #@classmethod
    def _parse_list_expr(cls, lexer):
        args = []
        token = lexer.next()
        if token.text != '(':
            raise CheckParseError("Expected '(' but got %r instead" % token)
        args, kwargs = cls._parse_argument_list(lexer)
        return list(args)
    _parse_list_expr = classmethod(_parse_list_expr)

class Check(tuple):
    """Represents a parse Check string

    A check is a python like mini-language defining a name and
    set of arguments and keyword arguments that define a series
    of constraints for some data check.  These are intrepreted
    by a higher level Validator object.

    Check BNF:

    <check>             ::= <name> <arguments>
    <arguments>         ::= ( <argument-list> ) | ""
    <argument-list>     ::= <argument> | <argument>,<argument>
    <argument>          ::= <identifier> | <integer> | <float> | <string>
    <identifier>        ::= (<letter>|"_") (<letter>|<digit>|"_")
    <integer>           ::= <digit> <digit>*
    <float>             ::= <digit>+ "." <digit>*
    <string>            ::= "'" stringitem* "'" | '"' stringitem* '"'
    <stringitem>        ::= <stringchar> | <escapeseq>
    <stringchar>        ::= <any source character except "\\" or newline or the
                             quote>
    <escapeseq>         ::= "\\" <any ASCII character>
    """

    name = property(lambda self: self[0])
    args = property(lambda self: self[1])
    kwargs = property(lambda self: self[2])
    default = property(lambda self: self[3])
    aliasof = property(lambda self: self[4])

    #@classmethod
    def parse(cls, check):
        """Parse a check and return a new Check instance"""
        name, args, kwargs = CheckParser.parse(check)
        default = kwargs.pop('default', missing)
        aliasof = kwargs.pop('aliasof', missing)
        return cls((name, args, kwargs, default, aliasof))
    parse = classmethod(parse)

    def __repr__(self):
        return "Check(name=%r, args=%r, kwargs=%r, default=%r, aliasof=%r)" % \
                (self.name, self.args, self.kwargs, self.default, self.aliasof)

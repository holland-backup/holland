# parse.py
import re
from holland.core.config.util import unquote
try:
    Scanner = re.Scanner
except AttributeError:
    from holland.core.util.pycompat import Scanner

class Token(object):
    """Lexer token"""
    def __init__(self, text, token_id, value):
        self.text = text
        self.id = token_id
        self.value = value

    def __repr__(self):
        return 'Token(text=%r, type=%r, value=%r)' % \
               (self.text, self.id, self.value)


class TokenGenerator(object):
    """Generate a token"""
    def __init__(self, token_id, conversion=str):
        self.token_id = token_id
        self.conversion = conversion

    def __call__(self, scanner, value):
        return Token(value, self.token_id, self.conversion(value))


class Lexer(object):
    """Simple lexer of an iterable of tokens"""
    def __init__(self, iterable):
        self.iterable = iter(iterable)

    def expect(self, *token_ids):
        token = self.next()
        if token.id not in token_ids:
            raise CheckError("Expected one of %r but got %r" % (token_ids, token))
        return token

    def next(self):
        try:
            tok = self.iterable.next()
            return tok
        except StopIteration:
            raise CheckError("Reached end-of-input when reading token")

    def __iter__(self):
        return self.iterable

class CheckError(Exception): pass

class CheckParser(object):
    """Parse the check DSL supported by ``Configspec``"""
    T_ID        = 1
    T_STR       = 2
    T_NUM       = 4
    T_SYM       = 16

    # rule patterns
    ident_re    = r'[a-zA-Z_][a-zA-Z0-9_]*'
    name_re     = r'[a-zA-Z_-][a-zA-Z0-9_-]*'
    #str_re      = r"'([^'\\]*(?:\\.[^'\\]*)*)'"
    #str_re      = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
    str_re      = (r"'([^'\\]*(?:\\.[^'\\]*)*)'"r'|"([^"\\]*(?:\\.[^"\\]*)*)"')
    float_re    = r'(?<!\.)\d+\.\d+'
    int_re      = r'\d+'
    sym_re      = r'[()=,]'
    space_re    = r'\s+'

    # scanner
    scanner = Scanner([
        (ident_re, TokenGenerator(T_ID)),
        #(name_re, TokenGenerator(T_STR)),
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
            raise CheckError("Failed to tokenize check at %r" % check)

        lexer = Lexer(tokens)

        method = lexer.next()
        if method.id != cls.T_ID:
            raise CheckError("Expected identifier as first token in check string but got %r")

        # bare-name check
        try:
            token = lexer.next()
        except CheckError:
            return method.value, (), {}

        if token.text != '(':
            raise CheckError("Expected '(' as token following method name")

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
                raise CheckError("Unexpected token %r" % token)

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
            raise CheckError("Expected check expression to end with ')' but got %r" % token)
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
            raise CheckError("Expected '(' but got %r instead" % token)
        args, kwargs = cls._parse_argument_list(lexer)
        return list(args)
    _parse_list_expr = classmethod(_parse_list_expr)

"""Functions for parsing S-Expressions"""
import re

from pygdl.parsing import ParseError
from pygdl.utils.containers import Bunch

S_EXPR_SYMBOLS = Bunch(
    BEGIN_TUPLE='(',
    END_TUPLE=')',
)


class MismatchedBracketError(ParseError):
    def __init__(self, type_):
        if type_ == 'extra':
            msg = "Extra bracket '" + S_EXPR_SYMBOLS.BEGIN_TUPLE + "'"
        elif type_ == 'missing':
            msg = "Missing bracket '" + S_EXPR_SYMBOLS.END_TUPLE + "'"
        else:
            raise AssertionError('Invalid type_ :' + type_)
        super().__init__(msg)


def parse_s_expressions(lines):
    return generate_s_expressions(tokenize_s_expression_lines(lines))


def tokenize_s_expression_lines(lines):
    """Tokenize lines containing S-expressions"""
    split_regex = \
        '([ ' + S_EXPR_SYMBOLS.BEGIN_TUPLE + S_EXPR_SYMBOLS.END_TUPLE + '])'

    for line in lines:
        for token in re.split(split_regex, line):
            stripped_token = token.strip()
            if len(stripped_token) > 0:
                yield stripped_token


def generate_s_expressions(tokens):
    """Generate S-expression from an iterator of tokens.

    For the purpose of this appliation, an S-expression is defined as
    either:
        * An atom
        * A tuple of S-expressions
    """
    s_expr_stack = []
    for token in tokens:
        if token == S_EXPR_SYMBOLS.BEGIN_TUPLE:
            new_s_expr = []
            if s_expr_stack:
                s_expr_stack[-1].append(new_s_expr)
            s_expr_stack.append(new_s_expr)

        elif token == S_EXPR_SYMBOLS.END_TUPLE:
            if not s_expr_stack:
                raise MismatchedBracketError('extra')
            if len(s_expr_stack) == 1:
                yield s_expr_stack[0]
            s_expr_stack.pop()

        else:
            s_expr_stack[-1].append(token)

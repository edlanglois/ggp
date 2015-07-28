"""Functions for parsing S-Expressions"""
import logging
import re

from pygdl.parsing import ParseError
from pygdl.utils.containers import Bunch

logger = logging.getLogger(__name__)

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
    """Generate S-expressions from an iterator of tokens.

    For the purpose of this appliation, an S-expression is defined as
    either:
        * An atom
        * A tuple of S-expressions
    """
    for token in tokens:
        if token == S_EXPR_SYMBOLS.BEGIN_TUPLE:
            yield list(generate_s_expressions(tokens))
        elif token == S_EXPR_SYMBOLS.END_TUPLE:
            break
        else:
            yield token

def to_s_expression_string(items):
    """Convert a nested iterable of items into an S-expression string."""
    if isinstance(items, str):
        return items

    return '{!s}{!s}{!s}'.format(
        S_EXPR_SYMBOLS.BEGIN_TUPLE,
        ' '.join(to_s_expression_string(item) for item in items),
        S_EXPR_SYMBOLS.END_TUPLE)


# TODO: Use a real parser
def prefix_functional_to_s_expressions(lines):
    return \
        prefix_functional_tokens_to_s_expressions(
            tokenize_prefix_functional_notation(lines))


def tokenize_prefix_functional_notation(lines):
    """Tokenize a set of lines in prefix functional notation

    In this notation, terms are either:
        ATOM
        ATOM(ARGS)
    where ARGS is a comma-separated list of 0 or more terms.
    """
    for line in lines:
        for token in re.split('([(),])', line):
            stripped_token = token.strip()
            if stripped_token not in (''):
                yield stripped_token


def prefix_functional_tokens_to_s_expressions(tokens):
    """Generate S-expressions from prefix functional tokens."""
    cur_term = None
    for token in tokens:
        if token == '(':
            assert cur_term is not None
            cur_term = ([cur_term] +
                        list(prefix_functional_tokens_to_s_expressions(tokens)))
        elif token == ')':
            break
        elif token == ',':
            assert cur_term is not None
            yield cur_term
            cur_term = None
        else:
            assert cur_term is None
            cur_term = token

    if cur_term is not None:
        yield cur_term

"""Functions for parsing and translating KIF-formatted data.

KIF uses prolog (actually datalog) symantic with a lisp syntax.
"""
import logging

from pygdl.parsing.exceptions import ParseError
from pygdl.parsing.sexpr import parse_s_expressions
from pygdl.utils.containers import Bunch
import pygdl.utils.iterators as iterator_utils

logger = logging.getLogger(__name__)

KIF_SYMBOLS = Bunch(
    VARIABLE_PREFIX='?',
    RULE='<=',
    COMMENT=';',
)
PROLOG_SYMBOLS = Bunch(
    RULE=':-',
)


class ArityError(ParseError):
    def __init__(self, func_name, expected_num_args, actual_num_args):
        self.func_name = func_name
        self.expected_num_args = expected_num_args
        self.actual_num_args = actual_num_args
        super().__init__(
            "Function '{!s}' called with {!s} arg(s) but expected {!s}".format(
                func_name, actual_num_args, expected_num_args))


def kif_to_s_expressions(kif_lines):
    """Parse KIF to S-expressions

    Given an iterator of KIF-formatted lines,
    yield equivalent lines of prolog.

    All comment lines are removed.
    """
    return parse_s_expressions(kif_remove_comments(kif_lines))


def single_kif_term_to_s_expression(term_string):
    try:
        return iterator_utils.get_and_ensure_single(
            kif_to_s_expressions([term_string]))

    except iterator_utils.LengthError:
        raise ValueError(
            'KIF string "{}" does not represent exactly one term'.format(
                term_string))


def kif_to_prolog(kif_lines):
    """Convert KIF format to prolog.

    Given an iterator of KIF-formatted lines,
    yields equivalent lines of prolog.

    All comment lines are removed.
    """
    return (kif_s_expr_to_prolog(s_expr)
            for s_expr in kif_to_s_expressions(kif_lines))


def single_kif_term_to_prolog(term_string):
    """Convert a single kif term string to a single prolog term.

    Raises ValueError if term_string doesn't represent exactly one term.
    """
    return kif_s_expr_to_prolog(single_kif_term_to_s_expression(term_string))


def kif_s_expr_to_prolog(s_expr):
    """Convert a KIF S-expression to the equivalent prolog text"""
    if (isinstance(s_expr, str)):
        s_expr = s_expr.lower()

        if s_expr[0] == KIF_SYMBOLS.VARIABLE_PREFIX:
            return s_expr[1:].upper()
        else:
            return s_expr

    elif s_expr[0] == KIF_SYMBOLS.RULE:
        if len(s_expr) < 2:
            raise ArityError(KIF_SYMBOLS.RULE, ">= 1", len(s_expr) - 1)

        head = s_expr[1]
        body = s_expr[2:]
        # If the body of a rule is empty in KIF
        # then the head is automatically true.
        if not body:
            body = ['true']
        return _kif_s_expr_to_prolog_rule(head, body)
    else:
        return _kif_s_expr_to_prolog_compound_term(s_expr[0], s_expr[1:])


def _kif_s_expr_to_prolog_rule(head, body):
    """Return a prolog rule string representing head <= all(body).

    Both head and body are KIF S-expressions.
    """
    return (
        kif_s_expr_to_prolog(head) +
        ' ' + PROLOG_SYMBOLS.RULE + ' ' +
        ', '.join(kif_s_expr_to_prolog(predicate_s_expr)
                  for predicate_s_expr in body)
    )


def _kif_s_expr_to_prolog_compound_term(functor, arguments):
    """Return a prolog compund term string represting functor(arguments).

    Both functor and arguments are KIF S-expressions.
    """
    return (
        kif_s_expr_to_prolog(functor) +
        '(' +
        ', '.join(kif_s_expr_to_prolog(arg_s_expr)
                  for arg_s_expr in arguments) +
        ')'
    )


def kif_remove_comments(lines):
    """Remove comments from KIF lines

    Removes lines that contain the comment character as the first
    non-whitespace character. Does not currently support removing comments
    from the end of lines nor does recognize and preserve multi-line
    strings.
    """
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line or stripped_line[0] == ';':
            continue
        yield stripped_line

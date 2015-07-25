"""Functions for working with KIF-formatted data.

KIF uses prolog (actually datalog) symantic with a lisp syntax.
"""
from pygdl.parsing import ParseError
from pygdl.sexpr import parse_s_expressions
from pygdl.utils.containers import Bunch

KIF_SYMBOLS = Bunch(
    VARIABLE_PREFIX='?',
    RULE='<=',
    COMMENT=';',
)
PROLOG_SYMBOLS = Bunch(
    RULE=':-',
)


class BadCapitilizationError(ParseError):
    def __init__(self, atom):
        super().__init__("Atom '" + atom + "' is not all in lowercase.")


def kif_to_prolog(kif_lines):
    """Convert KIF format to prolog.

    Given an iterator of KIF-formatted lines, yields equivalent lines of
    prolog.

    All comment lines are removed.
    """
    return (kif_s_expr_to_prolog(s_expr)
            for s_expr in
            parse_s_expressions(kif_remove_comments(kif_lines)))


def kif_s_expr_to_prolog(s_expr):
    """Convert a KIF S-expression to the equivalent prolog text"""
    if (isinstance(s_expr, str)):
        if (s_expr != s_expr.lower()):
            raise BadCapitilizationError(s_expr)

        if s_expr[0] == KIF_SYMBOLS.VARIABLE_PREFIX:
            return s_expr[1:].upper()
        else:
            return s_expr

    elif s_expr[0] == KIF_SYMBOLS.RULE:
        return kif_s_expr_to_prolog_rule(s_expr[1], s_expr[2:])
    else:
        return kif_s_expr_to_prolog_compound_term(s_expr[0], s_expr[1:])


def kif_s_expr_to_prolog_rule(head, body):
    """Return a prolog rule string representing head <= all(body).

    Both head and body are KIF S-expressions.
    """
    return (
        '(' + kif_s_expr_to_prolog(head) + ')' +
        ' ' + PROLOG_SYMBOLS.RULE + ' ' +
        ', '.join('(' + kif_s_expr_to_prolog(predicate_s_expr) + ')'
                  for predicate_s_expr in body)
    )


def kif_s_expr_to_prolog_compound_term(functor, arguments):
    """Return a prolog compund term string represting functor(arguments).

    Both functor and arguments are KIF S-expressions.
    """
    return (
        kif_s_expr_to_prolog(functor) +
        '(' +
        ', '.join('(' + kif_s_expr_to_prolog(arg_s_expr) + ')'
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

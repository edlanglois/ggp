"""Functions for working with KIF-formatted data.

KIF uses prolog (actually datalog) symantic with a lisp syntax.
"""
import re

from pygdl.utils.containers import Bunch

KIF_SYMBOLS = Bunch(
    BEGIN_TUPLE='(',
    END_TUPLE=')',
    VARIABLE_PREFIX='?',
    RULE='<=',
    COMMENT=';',
)
PROLOG_SYMBOLS = Bunch(
    RULE=':-',
)


class KIFSyntaxError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class MismatchedBracketError(KIFSyntaxError):
    def __init__(self, type_):
        if type_ == 'extra':
            msg = "Extra bracket '" + KIF_SYMBOLS.BEGIN_TUPLE + "'"
        elif type_ == 'missing':
            msg = "Missing bracket '" + KIF_SYMBOLS.END_TUPLE + "'"
        else:
            raise AssertionError('Invalid type_ :' + type_)
        super().__init__(msg)


class BadCapitilizationError(KIFSyntaxError):
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
            generate_s_expressions(
                tokenize_kif(
                    kif_remove_comments(
                        kif_lines
                    )
                )
            )
    )


def tokenize_kif(kif_lines):
    split_regex = \
        '([ ' + KIF_SYMBOLS.BEGIN_TUPLE + KIF_SYMBOLS.END_TUPLE + '])'

    for line in kif_lines:
        for token in re.split(split_regex, line):
            stripped_token = token.strip()
            if len(stripped_token) > 0:
                yield stripped_token


def generate_s_expressions(kif_tokens):
    """Generate S-expression from an iterator of KIF tokens.

    For the purpose of this appliation, an S-expression is defined as
    either:
        * An atom
        * A tuple of S-expressions
    """
    s_expr_stack = []
    for token in kif_tokens:
        if token == KIF_SYMBOLS.BEGIN_TUPLE:
            new_s_expr = []
            if s_expr_stack:
                s_expr_stack[-1].append(new_s_expr)
            s_expr_stack.append(new_s_expr)

        elif token == KIF_SYMBOLS.END_TUPLE:
            if not s_expr_stack:
                raise MismatchedBracketError('extra')
            if len(s_expr_stack) == 1:
                yield s_expr_stack[0]
            s_expr_stack.pop()

        else:
            s_expr_stack[-1].append(token)


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

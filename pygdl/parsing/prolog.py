"""Prolog parsing."""

from pygdl.parsing.sexpr import prefix_functional_to_s_expressions
import pygdl.utils.iterators as iterator_utils

def prolog_to_s_expressions(prolog_lines):
    """Parse prolog to S-expressions.

    The prolog lines must not contain comments.
    """
    return prefix_functional_to_s_expressions(prolog_lines)

def single_prolog_term_to_s_expression(term_string):
    try:
        return iterator_utils.get_and_ensure_single(
            prolog_to_s_expressions([term_string]))

    except iterator_utils.LengthError:
        raise ValueError(
            'Prolog string "{}" does not represent exactly one term'.format(
                term_string))

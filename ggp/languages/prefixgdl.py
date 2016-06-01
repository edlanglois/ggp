"""Prefix Game Description Language (GDL)"""
from functools import reduce

from pyparsing import (
    Forward,
    Group,
    Literal,
    Suppress,
    White,
    Word,
    ZeroOrMore,
    printables,
    quotedString,
)
import swilite

__all__ = [
    'prefix_gdl_statement_to_prolog',
    'prefix_gdl_statements_to_prolog',
    'prolog_term_to_prefix_gdl',
]


class PrefixGdlParser():
    def __init__(self):
        super().__init__()
        self.lpar = Literal('(')('lpar')
        self.rpar = Literal(')')('rpar')
        self.qmark = Literal('?')('qmark')

        self.word_chars = ''.join(c for c in printables if c not in ('()'))
        self.word = Word(self.word_chars) | quotedString
        self.variable = (
            Suppress(self.qmark) + ~White() + self.word)('variable')

        self.atom = self.word('atom')

        self.term = Forward()
        self.terms = Group(ZeroOrMore(self.term))

        self.predicate_name = self.word('name')

        self.compound_term = Group(
            Suppress(self.lpar) +
            self.predicate_name +
            self.terms('arguments') +
            Suppress(self.rpar)
        )('compound_term')

        self.term << (self.compound_term | self.variable | self.atom)

        self.statement = self.term('statement')
        self.statements = Group(ZeroOrMore(self.statement))('statements')


class PrefixGdlToProlog(PrefixGdlParser):
    def __init__(self):
        super().__init__()
        self.variables = {}

        def variable_action(toks):
            variable_name = toks.variable[0]
            try:
                return self.variables[variable_name]
            except KeyError:
                var = swilite.Term()
                self.variables[variable_name] = var
                return var

        def statement_action(toks):
            # Reset variables after each statement
            self.variables = {}
            return toks.statement

        self.variable.addParseAction(variable_action)
        self.atom.addParseAction(self._atom_action)
        self.compound_term.addParseAction(self._compound_term_action)
        self.statement.addParseAction(statement_action)
        self.statements.addParseAction(self._statements_action)

    @staticmethod
    def _atom_action(toks):
        return swilite.Term.from_atom_name(toks.atom)

    @staticmethod
    def _compound_term_action(toks):
        name = toks.compound_term.name
        args = toks.compound_term.arguments

        # Translate GDL rule operator to Prolog rule operator
        if name == '<=':
            name = ':-'
            # '<=' is variadic while ':-' has arity 2
            args = (args[0], reduce(lambda b, a: a & b, reversed(args[1:])))

        return swilite.Term.from_cons_functor(
            swilite.Functor(name, len(args)), *args)

    @staticmethod
    def _statements_action(toks):
        return swilite.Term.from_list_terms(toks.statements)


_prefix_gdl_to_prolog = PrefixGdlToProlog()


def prefix_gdl_statements_to_prolog(gdl_statements):
    """Translate multiple GDL statements to a prolog term.

    Args:
        gdl_statements (str): A collection of GDL statements to translate.

    Returns:
        swilite.Term: Term representing a list of the translated
            statements.
    """
    return _prefix_gdl_to_prolog.statements.parseString(
        gdl_statements, parseAll=True).statements


def prefix_gdl_statement_to_prolog(gdl_statement):
    """Translate a single GDL statement to a prolog term.

    Args:
        gdl_statement (str): A GDL statement to translate.

    Returns:
        swilite.Term: Term representing the translated statement.
    """
    return _prefix_gdl_to_prolog.statement.parseString(
        gdl_statement, parseAll=True).statement


def prolog_term_to_prefix_gdl(term):
    if term.is_compound():
        name_atom, arity = term.get_compound_name_arity()
        name = str(name_atom)
        args = [prolog_term_to_prefix_gdl(term.get_arg(i))
                for i in range(arity)]

        if name == ':-':
            # TODO:
            # name = '<='
            # Unpack arity-2 arguments to a single variadic arguments list
            raise NotImplementedError(repr(term))
        return '({})'.format(' '.join([name, *args]))

    elif term.is_variable():
        return '?' + str(term)
    elif term.is_atom():
        return term.get_atom_name()
    elif term.is_numeric():
        return str(term)
    else:
        raise NotImplementedError(repr(term))

"""Prefix Game Description Language (GDL)"""
import itertools
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

from ggp.utils.comparison import TypedEqualityMixin


class PrefixGdlTerm(TypedEqualityMixin):
    pass


class PrefixGdlAtomicTerm(PrefixGdlTerm):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '{class_}(name={name!r})'.format(
            class_=self.__class__.__name__,
            name=self.name)


class PrefixGdlAtom(PrefixGdlAtomicTerm):
    def __init__(self, name):
        if name[0] == '?':
            raise ValueError('{cls} name cannot begin with ?'.format(
                cls=PrefixGdlAtom.__name__))
        self.name = name

    def __str__(self):
        return self.name


class PrefixGdlVariable(PrefixGdlAtomicTerm):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return '?' + self.name


class PrefixGdlCompoundTerm(PrefixGdlTerm):
    def __init__(self, name, args):
        self.name = name
        self.args = tuple(args)

    def __str__(self):
        return '({})'.format(' '.join(
            str(x) for x in itertools.chain((self.name,), self.args)))

    def __repr__(self):
        return '{cls}(name={name!r}, args=({args}))'.format(
            cls=self.__class__.__name__,
            name=self.name,
            args=', '.join(repr(x) for x in self.args))


class PrefixGdlStatements(list):
    def __str__(self):
        return ' '.join(str(x) for x in self)

    def __repr__(self):
        return '{}([{}])'.format(
            self.__class__.__name__,
            ', '.join(repr(x) for x in self))


class PrefixGdlParser(object):
    def __init__(self):
        super().__init__()
        self.lpar = Literal('(')('lpar')
        self.rpar = Literal(')')('rpar')
        self.qmark = Literal('?')('qmark')

        self.word_chars = ''.join(c for c in printables if c not in ('()'))
        self.word = Word(self.word_chars) | quotedString
        self.variable = (
            Suppress(self.qmark) + ~White() + self.word)('variable')
        self.variable.addParseAction(self._variable_action)

        self.atom = self.word('atom')
        self.atom.addParseAction(self._atom_action)

        self.term = Forward()
        self.terms = Group(ZeroOrMore(self.term))

        self.predicate_name = self.word('name')

        self.compound_term = Group(
            Suppress(self.lpar) +
            self.predicate_name +
            self.terms('arguments') +
            Suppress(self.rpar)
        )('compound_term')
        self.compound_term.addParseAction(self._compound_term_action)

        self.term << (self.compound_term | self.variable | self.atom)

        self.statements = self.terms('statements')
        self.statements.addParseAction(self._statements_action)

    def parse(self, instring):
        return self.statements.parseString(instring, parseAll=True).statements

    @staticmethod
    def _atom_action(toks):
        return PrefixGdlAtom(name=toks.atom)

    @staticmethod
    def _variable_action(toks):
        return PrefixGdlVariable(name=toks.variable[0])

    @staticmethod
    def _compound_term_action(toks):
        return PrefixGdlCompoundTerm(
            name=toks.compound_term.name,
            args=toks.compound_term.arguments)

    @staticmethod
    def _statements_action(toks):
        # Pyparsing extracts tuple results into ParsedResults.  Since
        # PrefixGdlStatements is a tuple, we wrap it in another tuple before
        # returning, which will be extracted into a ParsedResults, leaving the
        # PrefixGdlStatements intact.
        return (PrefixGdlStatements(toks.statements),)

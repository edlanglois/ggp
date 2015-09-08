"""Prefix Game Description Language (GDL)"""
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

        self.statements = self.terms('statements')

    def parse(self, instring):
        return self.statements.parseString(instring, parseAll=True).statements

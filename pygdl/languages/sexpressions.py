"""S-Expressions"""
from pyparsing import (
    Forward,
    Group,
    Literal,
    Suppress,
    Word,
    ZeroOrMore,
    printables,
    quotedString,
)


class SExpression(tuple):
    def __str__(self):
        return '({})'.format(
            ' '.join(str(subexpr) for subexpr in self))

    def __repr__(self):
        return '{name}({arg!s})'.format(
            name=SExpression.__name__,
            arg=tuple(self))


class SExpressionList(tuple):
    def __str__(self):
        return ' '.join(str(sexpr) for sexpr in self)

    def __repr__(self):
        return '{name}({arg!s})'.format(
            name=SExpressionList.__name__,
            arg=tuple(self))


class SExpressionParser(object):
    def __init__(self):
        self.lpar = Literal('(')
        self.rpar = Literal(')')

        self.word_chars = ''.join(c for c in printables if c not in ('()'))
        self.word = Word(self.word_chars) | quotedString
        self.atom = self.word

        self.expression = Forward()

        self.composite_expression = (
            Suppress(self.lpar) +
            ZeroOrMore(self.expression) +
            Suppress(self.rpar))('composite_expression')
        self.composite_expression.addParseAction(
            self._composite_expression_to_tuple)

        self.expression << (self.atom | self.composite_expression)

        self.expressions = Group(ZeroOrMore(self.expression))('expressions')
        self.expressions.addParseAction(self._expressions_to_tuple)

    def parse_expression(self, instring):
        return self.expression.parseString(instring, parseAll=True)[0]

    def parse_expressions(self, instring):
        return self.expressions.parseString(instring, parseAll=True)[0]

    @staticmethod
    def _composite_expression_to_tuple(toks):
        return SExpression(toks.composite_expression)

    @staticmethod
    def _expressions_to_tuple(toks):
        return SExpressionList(toks.expressions)

s_expression_parser = SExpressionParser()

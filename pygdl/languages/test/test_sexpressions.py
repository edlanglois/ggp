from nose.tools import (
    assert_equal,
    assert_raises,
)

from pyparsing import ParseException

from pygdl.languages.sexpressions import (
    SExpression,
    SExpressionList,
    SExpressionParser,
)


def test_s_expression_one_arg():
    s = SExpression(('one',))
    assert_equal(len(s), 1)
    assert_equal(s[0], 'one')
    assert_equal(str(s), '(one)')
    assert_equal(repr(s), "SExpression(('one',))")


def test_s_expression_two_args():
    s = SExpression(('one', '2'))
    assert_equal(len(s), 2)
    assert_equal(s[0], 'one')
    assert_equal(s[1], '2')
    assert_equal(str(s), '(one 2)')
    assert_equal(repr(s), "SExpression(('one', '2'))")


def test_s_expression_empty():
    s = SExpression(())
    assert_equal(len(s), 0)
    assert_equal(str(s), '()')
    assert_equal(repr(s), "SExpression(())")


def test_s_expression_nested():
    s = SExpression((SExpression(('foo', '1')), 'bar'))
    assert_equal(len(s), 2)
    assert_equal(len(s[0]), 2)
    assert_equal(s[0][0], 'foo')
    assert_equal(s[0][1], '1')
    assert_equal(s[1], 'bar')
    assert_equal(str(s), '((foo 1) bar)')
    assert_equal(repr(s),
                 "SExpression((SExpression(('foo', '1')), 'bar'))")


def test_s_expression_list():
    s_foo = SExpression(('foo',))
    s_bar = SExpression(('bar', 'baz'))
    sl = SExpressionList((s_foo, s_bar))
    assert_equal(len(sl), 2)
    assert_equal(sl[0], s_foo)
    assert_equal(sl[1], s_bar)
    assert_equal(str(sl), '(foo) (bar baz)')
    assert_equal(repr(sl), 'SExpressionList(({!r}, {!r}))'.format(s_foo, s_bar))


class TestSExpressionParser():
    def setUp(self):
        self.parser = SExpressionParser()

    def test_expression_one_word(self):
        assert_equal(self.parser.parse_expression('word'),
                     'word')

    def test_expression_empty_string(self):
        with assert_raises(ParseException):
            self.parser.parse_expression('')

    def test_expression_multiple_words(self):
        with assert_raises(ParseException):
            self.parser.parse_expression('two words')

    def test_expression_compound_empty(self):
        assert_equal(self.parser.parse_expression('()'),
                     SExpression(()))

    def test_expression_compound_one_arg(self):
        assert_equal(self.parser.parse_expression('(foo)'),
                     SExpression(('foo',)))

    def test_expression_compound_three_args(self):
        assert_equal(self.parser.parse_expression('(arg0 arg1 arg2)'),
                     SExpression(('arg0', 'arg1', 'arg2')))

    def test_expression_compound_nested_once(self):
        assert_equal(self.parser.parse_expression('((foo))'),
                     SExpression((SExpression(('foo',)),)))

    def test_expression_compound_nested_deep(self):
        depth = 100
        expected = 'foo'
        for _ in range(depth):
            expected = SExpression((expected,))
        assert_equal(
            self.parser.parse_expression('(' * depth + 'foo' + ')' * depth),
            expected)

    def test_expression_compound_nested_complex(self):
        assert_equal(self.parser.parse_expression('((foo 1) (bar (baz 2)))'),
                     SExpression((SExpression(('foo', '1')),
                                  SExpression(('bar',
                                               SExpression(('baz', '2')))))))

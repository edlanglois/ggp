import difflib

from nose.tools import (
    assert_equal,
    assert_raises,
    assert_sequence_equal,
)

from ggp.languages.prefixgdl import (
    PrefixGdlAtom,
    PrefixGdlCompoundTerm,
    PrefixGdlVariable,
)

from ggp.languages.prolog import (
    PrologAtom,
    PrologCompoundTerm,
    PrologInteger,
    PrologOperatorTerm,
    PrologTerm,
    PrologVariable,
)

from ggp.languages.translation.pgdl_prolog import (
    PrefixGdlToProlog,
    PrologToPrefixGdl,
)


class BaseTestPrefixGdlToProlog():
    def check_translate(self, prefix_gdl, *expected_terms):
        assert_sequence_equal(self.translator.translate(prefix_gdl),
                              expected_terms)

    def test_translate_common(self):
        yield self.check_translate, 'abc', PrologAtom('abc')
        yield (self.check_translate, 'abc def',
               PrologAtom('abc'), PrologAtom('def'))
        yield self.check_translate, 'Abc', PrologAtom('Abc')
        yield self.check_translate, '_abc', PrologAtom('_abc')
        yield self.check_translate, '_', PrologAtom('_')
        yield self.check_translate, '1', PrologAtom('1')
        yield self.check_translate, '(foo)', PrologCompoundTerm('foo', args=())
        yield (self.check_translate, '(foo bar)',
               PrologCompoundTerm('foo', args=(PrologAtom('bar'),)))
        yield (self.check_translate, '(<= a b)',
               PrologOperatorTerm(':-', args=(
                   PrologAtom('a'), PrologAtom('b'))))
        yield (self.check_translate, '(<= a b c)',
               PrologOperatorTerm(':-', args=(
                   PrologAtom('a'),
                   PrologTerm.and_(PrologAtom('b'), PrologAtom('c')))))

    def check_translate_to_single_term(self, prefix_gdl, expected_term):
        assert_equal(self.translator.translate_to_single_term(prefix_gdl),
                     expected_term)

    def check_translate_to_single_term_fails(self, prefix_gdl):
        with assert_raises(ValueError):
            self.translator.translate_to_single_term(prefix_gdl)

    def test_translate_to_single_term_common(self):
        yield self.check_translate_to_single_term, 'abc', PrologAtom('abc')
        yield (self.check_translate_to_single_term, '(foo)',
               PrologCompoundTerm('foo', args=()))
        yield (self.check_translate, '(foo bar)',
               PrologCompoundTerm('foo', args=(PrologAtom('bar'),)))
        yield self.check_translate_to_single_term_fails, ''
        yield self.check_translate_to_single_term_fails, 'abc def'


class TestPrefixGdlToPrologBijective(BaseTestPrefixGdlToProlog):
    def setUp(self):
        self.translator = PrefixGdlToProlog(bijective=True)

    def test_translate(self):
        yield self.check_translate, '?var', PrologVariable('_var')
        yield self.check_translate, '?Var', PrologVariable('_Var')
        yield self.check_translate, '?_', PrologVariable('__')
        yield self.check_translate, '?_var', PrologVariable('__var')
        yield self.check_translate, '?123', PrologVariable('_123')
        yield (self.check_translate,
               '(a (b c) (d (e f ?g)))',
               PrologCompoundTerm(
                   'a', args=(
                       PrologCompoundTerm('b', args=(
                           PrologAtom('c'),)),
                       PrologCompoundTerm('d', args=(
                           PrologCompoundTerm('e', args=(
                               PrologAtom('f'),
                               PrologVariable('_g'))),)))))


class TestPrefixGdlToPrologNonBijective(BaseTestPrefixGdlToProlog):
    def setUp(self):
        self.translator = PrefixGdlToProlog(bijective=False)

    def test_translate(self):
        yield self.check_translate, '?var', PrologVariable('Var')
        yield self.check_translate, '?Var', PrologVariable('Var')
        yield self.check_translate, '?_', PrologVariable('_')
        yield self.check_translate, '?_var', PrologVariable('_var')
        yield self.check_translate, '?123', PrologVariable('_123')
        yield (self.check_translate,
               '(a (b c) (d (e f ?g)))',
               PrologCompoundTerm(
                   'a', args=(
                       PrologCompoundTerm('b', args=(
                           PrologAtom('c'),)),
                       PrologCompoundTerm('d', args=(
                           PrologCompoundTerm('e', args=(
                               PrologAtom('f'),
                               PrologVariable('G'))),)))))


class BaseTestPrologToPrefixGdl():
    def check_translate_parsed_prolog_term(self, prolog_term,
                                           expected_gdl_term):
        translated = self.translator.translate_parsed_prolog_term(prolog_term)
        assert_equal(translated, expected_gdl_term,
                     msg='\n' + '\n'.join(difflib.ndiff(
                         [repr(translated)], [repr(expected_gdl_term)])))

    def check_cannot_translate(self, prolog_term):
        with assert_raises(ValueError):
            self.translator.translate_parsed_prolog_term(prolog_term)

    def test_translate_parsed_prolog_term_common(self):
        yield (self.check_translate_parsed_prolog_term,
               PrologAtom('abc'), PrefixGdlAtom('abc'))
        yield (self.check_translate_parsed_prolog_term,
               PrologAtom('Abc'), PrefixGdlAtom('Abc'))
        yield (self.check_translate_parsed_prolog_term,
               PrologAtom('_abc'), PrefixGdlAtom('_abc'))
        yield (self.check_translate_parsed_prolog_term,
               PrologAtom('_'), PrefixGdlAtom('_'))
        yield (self.check_translate_parsed_prolog_term,
               PrologAtom('1'), PrefixGdlAtom('1'))
        yield (self.check_translate_parsed_prolog_term,
               PrologInteger('1'), PrefixGdlAtom('1'))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm('foo', ()),
               PrefixGdlCompoundTerm('foo', ()))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm('foo', (PrologAtom('bar'),)),
               PrefixGdlCompoundTerm('foo', (PrefixGdlAtom('bar'),)))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm(':-', (PrologAtom('a'), PrologAtom('b'))),
               PrefixGdlCompoundTerm('<=', (PrefixGdlAtom('a'),
                                            PrefixGdlAtom('b'))))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm(':-', (
                   PrologAtom('a'),
                   PrologTerm.and_(PrologAtom('b'), PrologAtom('c')))),
               PrefixGdlCompoundTerm('<=', (
                   PrefixGdlAtom('a'), PrefixGdlAtom('b'), PrefixGdlAtom('c'))))

    def test_cannot_translate_common(self):
        yield self.check_cannot_translate, PrologAtom('?')
        yield self.check_cannot_translate, PrologAtom('?abc')


class TestPrologToPrefixGdlBijective(BaseTestPrologToPrefixGdl):
    def setUp(self):
        self.translator = PrologToPrefixGdl(bijective=True)

    def test_translate_parsed_prolog_term(self):
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_var'), PrefixGdlVariable('var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_Var'), PrefixGdlVariable('Var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('__'), PrefixGdlVariable('_'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('__var'), PrefixGdlVariable('_var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_123'), PrefixGdlVariable('123'))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm(
                   'a', args=(
                       PrologCompoundTerm('b', args=(
                           PrologAtom('c'),)),
                       PrologCompoundTerm('d', args=(
                           PrologCompoundTerm('e', args=(
                               PrologAtom('f'),
                               PrologVariable('_g'))),)))),
               PrefixGdlCompoundTerm(
                   'a', args=(
                       PrefixGdlCompoundTerm('b', args=(
                           PrefixGdlAtom('c'),)),
                       PrefixGdlCompoundTerm('d', args=(
                           PrefixGdlCompoundTerm('e', args=(
                               PrefixGdlAtom('f'),
                               PrefixGdlVariable('g'))),)))))

    def test_cannot_translate(self):
        yield self.check_cannot_translate, PrologVariable('_')
        yield self.check_cannot_translate, PrologVariable('X')
        yield self.check_cannot_translate, PrologVariable('Var')


class TestPrologToPrefixGdlNonBijective(BaseTestPrologToPrefixGdl):
    def setUp(self):
        self.translator = PrologToPrefixGdl(bijective=False)

    def test_translate_parsed_prolog_term(self):
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_var'), PrefixGdlVariable('_var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_Var'), PrefixGdlVariable('_Var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('__'), PrefixGdlVariable('__'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('__var'), PrefixGdlVariable('__var'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_123'), PrefixGdlVariable('_123'))
        yield (self.check_translate_parsed_prolog_term,
               PrologCompoundTerm(
                   'a', args=(
                       PrologCompoundTerm('b', args=(
                           PrologAtom('c'),)),
                       PrologCompoundTerm('d', args=(
                           PrologCompoundTerm('e', args=(
                               PrologAtom('f'),
                               PrologVariable('_g'))),)))),
               PrefixGdlCompoundTerm(
                   'a', args=(
                       PrefixGdlCompoundTerm('b', args=(
                           PrefixGdlAtom('c'),)),
                       PrefixGdlCompoundTerm('d', args=(
                           PrefixGdlCompoundTerm('e', args=(
                               PrefixGdlAtom('f'),
                               PrefixGdlVariable('_g'))),)))))

        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('_'), PrefixGdlVariable('_'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('X'), PrefixGdlVariable('x'))
        yield (self.check_translate_parsed_prolog_term,
               PrologVariable('Var'), PrefixGdlVariable('var'))

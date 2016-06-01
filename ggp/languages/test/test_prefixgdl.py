from nose.tools import (
    assert_equal,
    assert_not_in,
    assert_true,
)
from swilite import Term, Frame, Functor

from ggp.languages.prefixgdl import (
    prefix_gdl_statement_to_prolog,
    prefix_gdl_statements_to_prolog,
    prolog_term_to_prefix_gdl,
)


class TestPrefixGdlStatementToPrologAtom():
    def setUp(self):
        self.frame = Frame()

    def tearDown(self):
        self.frame.discard()

    @staticmethod
    def check_parse_statement(target, gdl_statement):
        assert_equal(prefix_gdl_statement_to_prolog(gdl_statement),
                     target)

    @staticmethod
    def check_parse_statements(target, *gdl_statements):
        assert_equal(
            prefix_gdl_statements_to_prolog('\n'.join(gdl_statements)),
            target)

    @staticmethod
    def check_parse_atoms(*atoms):
        terms = []
        for atom in atoms:
            term = Term.from_atom_name(atom)
            terms.append(term)
            TestPrefixGdlStatementToPrologAtom.check_parse_statement(
                term, atom)

        TestPrefixGdlStatementToPrologAtom.check_parse_statements(
            Term.from_list_terms(terms), '\n'.join(atoms))

    def test_empty_string(self):
        self.check_parse_atoms()

    def test_atom_word(self):
        self.check_parse_atoms('word')

    def test_atom_multiple_words(self):
        self.check_parse_atoms('here', 'are', 'some', 'words')

    def test_atom_number(self):
        self.check_parse_atoms('123')

    def test_atom_interior_question_mark(self):
        self.check_parse_atoms('foo?bar')

    def test_atom_suffix_question_mark(self):
        self.check_parse_atoms('foo?')

    def test_atom_interior_comma(self):
        self.check_parse_atoms('foo,bar')

    def test_atom_integer(self):
        self.check_parse_atoms('1', '0', '-1')

    @staticmethod
    def check_parse_variables(*variables):
        variables = ['?' + var for var in variables]
        for variable in variables:
            assert_true(prefix_gdl_statement_to_prolog(variable).is_variable())

        term_list = prefix_gdl_statements_to_prolog('\n'.join(variables))
        terms = []
        # Check that all variable terms are unique
        while not term_list.is_nil():
            term = term_list.get_arg(0)
            assert_not_in(term, terms)
            terms.append(term)
            term_list = term_list.get_arg(1)

        assert_equal(len(terms), len(variables))

    def test_variable_word(self):
        self.check_parse_variables('word')

    def test_variables(self):
        self.check_parse_variables('some', 'variables', 'here')

    def test_variables_repeating(self):
        self.check_parse_variables('a', 'a', 'b', 'a', 'b')

    def test_variables_caps(self):
        self.check_parse_variables('Aa')

    def test_variables_underscore(self):
        self.check_parse_variables('_b')

    def test_variables_numbers(self):
        self.check_parse_variables('123')

    def test_compound_term_one_atom(self):
        assert_equal(prefix_gdl_statement_to_prolog('(foo arg)'),
                     Functor('foo', 1)(Term.from_atom_name('arg')))

    def test_compound_term_mixed_atomic(self):
        term = prefix_gdl_statement_to_prolog('(foo arg1 ?arg2 arg3)')
        assert_equal(term.get_functor(), Functor('foo', 3))
        assert_equal(term.get_arg(0), Term.from_atom_name('arg1'))
        assert_true(term.get_arg(1).is_variable())
        assert_equal(term.get_arg(2), Term.from_atom_name('arg3'))

    def test_compound_repeated_variable(self):
        term = prefix_gdl_statement_to_prolog('(foo ?X ?X)')
        assert_equal(term.get_functor(), Functor('foo', 2))
        assert_true(term.get_arg(0).is_variable())
        assert_true(term.get_arg(1).is_variable())
        assert_equal(term.get_arg(0), term.get_arg(1))

    def test_compound_term_nexted(self):
        assert_equal(
            prefix_gdl_statement_to_prolog('(foo (bar 1 2) (baz 3))'),
            Functor('foo', 2)(Functor('bar', 2)(Term.from_atom_name('1'),
                                                Term.from_atom_name('2')),
                              Functor('baz', 1)(Term.from_atom_name('3'))))

    def test_compound_term_no_args(self):
        assert_equal(prefix_gdl_statement_to_prolog('(foo)'),
                     Functor('foo', 0)())

    def test_rule_symbol_translation(self):
        assert_equal(prefix_gdl_statement_to_prolog('(<= foo bar)'),
                     Functor(':-', 2)(Term.from_atom_name('foo'),
                                      Term.from_atom_name('bar')))

    def test_rule_variadic_translation(self):
        rule = Functor(':-', 2)
        and_ = Functor(',', 2)
        assert_equal(
            prefix_gdl_statement_to_prolog('(<= foo 1 2 3 4)'),
            rule(Term.from_atom_name('foo'),
                 and_(Term.from_atom_name('1'),
                      and_(Term.from_atom_name('2'),
                           and_(Term.from_atom_name('3'),
                                Term.from_atom_name('4'))))))


class TestPrologTermToPrefixGdl():
    def setUp(self):
        self.frame = Frame()

    def tearDown(self):
        self.frame.discard()

    def test_atom_term(self):
        assert_equal(prolog_term_to_prefix_gdl(Term.from_atom_name('foo')),
                     'foo')

    def test_variable_term(self):
        assert_equal(prolog_term_to_prefix_gdl(Term())[0], '?')

    def test_compound_term(self):
        assert_equal(prolog_term_to_prefix_gdl(
            Functor('foo', 2)(Term.from_atom_name('bar'),
                              Term.from_atom_name('2'))),
            '(foo bar 2)')

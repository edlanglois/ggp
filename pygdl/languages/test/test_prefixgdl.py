from nose.tools import (
    assert_equal,
    assert_is_instance,
    assert_not_equal,
)

from pygdl.languages.prefixgdl import (
    PrefixGdlAtom,
    PrefixGdlAtomicTerm,
    PrefixGdlCompoundTerm,
    PrefixGdlParser,
    PrefixGdlStatements,
    PrefixGdlVariable,
)


def test_prefix_gdl_atomic_equality():
    assert_equal(PrefixGdlAtom('atom'), PrefixGdlAtom('atom'))
    assert_equal(PrefixGdlVariable('var'), PrefixGdlVariable('var'))
    assert_not_equal(PrefixGdlAtom('foo'), PrefixGdlAtom('bar'))
    assert_not_equal(PrefixGdlVariable('foo'), PrefixGdlVariable('bar'))
    assert_not_equal(PrefixGdlAtom('name'), PrefixGdlVariable('name'))


def test_prefix_gdl_atom():
    atom = PrefixGdlAtom('atom')
    assert_equal(atom.name, 'atom')
    assert_equal(str(atom), 'atom')
    assert_equal(repr(atom), "PrefixGdlAtom(name='atom')")


def test_prefix_gdl_variable():
    variable = PrefixGdlVariable('var')
    assert_equal(variable.name, 'var')
    assert_equal(str(variable), '?var')
    assert_equal(repr(variable), "PrefixGdlVariable(name='var')")


def test_prefix_gdl_compound_term():
    compound_term = PrefixGdlCompoundTerm('foo', ('arg1', 'arg2'))
    assert_equal(compound_term.name, 'foo')
    assert_equal(len(compound_term.args), 2)
    assert_equal(compound_term.args[0], 'arg1')
    assert_equal(compound_term.args[1], 'arg2')
    assert_equal(str(compound_term), '(foo arg1 arg2)')
    assert_equal(repr(compound_term),
                 "PrefixGdlCompoundTerm(name='foo', args=('arg1', 'arg2'))")


def test_prefix_gdl_compound_term_no_args():
    compound_term = PrefixGdlCompoundTerm('foo', tuple())
    assert_equal(compound_term.name, 'foo')
    assert_equal(len(compound_term.args), 0)
    assert_equal(str(compound_term), '(foo)')


def test_prefix_gdl_compound_term_nested():
    compound_term = PrefixGdlCompoundTerm('foo', (
        PrefixGdlCompoundTerm('bar', ('1', '2')),
        PrefixGdlCompoundTerm('baz', ('3'))))
    assert_equal(compound_term.name, 'foo')
    assert_equal(len(compound_term.args), 2)
    assert_equal(compound_term.args[0].name, 'bar')
    assert_equal(len(compound_term.args[0].args), 2)
    assert_equal(compound_term.args[0].args[0], '1')
    assert_equal(compound_term.args[0].args[1], '2')
    assert_equal(compound_term.args[1].name, 'baz')
    assert_equal(len(compound_term.args[1].args), 1)
    assert_equal(compound_term.args[1].args[0], '3')
    assert_equal(str(compound_term), '(foo (bar 1 2) (baz 3))')


def test_prefix_gdl_statements():
    a = PrefixGdlAtom('a')
    b = PrefixGdlAtom('b')
    statements = PrefixGdlStatements([a, b])
    assert_equal(len(statements), 2)
    assert_is_instance(statements[0], PrefixGdlAtom)
    assert_equal(statements[0].name, 'a')
    assert_is_instance(statements[1], PrefixGdlAtom)
    assert_equal(statements[1].name, 'b')
    assert_equal(str(statements), 'a b')
    assert_equal(repr(statements),
                 "PrefixGdlStatements([{!r}, {!r}])".format(a, b))


class TestPrefixGdlParser():
    def setUp(self):
        self.parser = PrefixGdlParser()

    def check_parse_atoms(self, *atoms):
        prefix_gdl_string = ' '.join(atoms)
        return self.check_parse_atomic_terms(
            prefix_gdl_string, atoms, PrefixGdlAtom)

    def check_parse_variables(self, *variables):
        prefix_gdl_string = ' '.join('?' + var for var in variables)
        return self.check_parse_atomic_terms(
            prefix_gdl_string, variables, PrefixGdlVariable)

    def check_parse_atomic_terms(self, prefix_gdl_string, terms, term_type):
        print('Parsing string: {!r}'.format(prefix_gdl_string))
        parsed = self.parser.parse(prefix_gdl_string)
        assert_equal(len(parsed), len(terms))
        assert_is_instance(parsed, PrefixGdlStatements)
        # Sequence access
        for parsed_elem, term in zip(parsed, terms):
            assert_equal(parsed_elem, term_type(term))

        # Index access
        for i, term in enumerate(terms):
            assert_equal(parsed[i], term_type(term))

    def check_parse_structure(self, parsed, structure):
        print(type(parsed))
        print(parsed)
        if isinstance(structure, PrefixGdlAtomicTerm):
            assert_equal(parsed, structure)
        else:
            assert_is_instance(parsed, PrefixGdlCompoundTerm)
            assert_equal(parsed.name, structure[0])
            assert_equal(len(parsed.args), len(structure) - 1)
            for parsed_elem, structure_elem in zip(parsed.args, structure[1:]):
                self.check_parse_structure(parsed_elem, structure_elem)

    def check_parse_structure_single_statement(self, parsed, structure):
        print(type(parsed))
        print(parsed)
        assert_is_instance(parsed, PrefixGdlStatements)
        assert_equal(len(parsed), 1)
        self.check_parse_structure(parsed[0], structure)

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

    def test_variable_word(self):
        self.check_parse_variables('word')

    def test_variables(self):
        self.check_parse_variables('some', 'variables', 'here')

    def test_compound_term_one_atom(self):
        parsed = self.parser.parse('(foo arg)')
        self.check_parse_structure_single_statement(
            parsed,
            ['foo', PrefixGdlAtom('arg')])

    def test_compound_term_mixed_atomic(self):
        parsed = self.parser.parse('(foo arg1 ?arg2 arg3)')
        self.check_parse_structure_single_statement(
            parsed,
            ['foo', PrefixGdlAtom('arg1'), PrefixGdlVariable('arg2'),
             PrefixGdlAtom('arg3')])

    def test_compound_term_nested(self):
        parsed = self.parser.parse('(foo (bar 1 2) (baz 3))')
        self.check_parse_structure_single_statement(
            parsed,
            ['foo', ['bar', PrefixGdlAtom('1'), PrefixGdlAtom('2')],
             ['baz', PrefixGdlAtom('3')]])

    def test_compound_term_no_args(self):
        parsed = self.parser.parse('(foo)')
        self.check_parse_structure_single_statement(
            parsed, ['foo'])

from nose.tools import (
    assert_equal,
    assert_in,
    assert_is_instance,
    assert_raises,
    assert_sequence_equal,
)

from pygdl.languages.prolog import (
    PrologAtom,
    PrologCompoundTerm,
    PrologFloat,
    PrologInteger,
    PrologList,
    PrologOperatorTerm,
    PrologString,
    PrologTerm,
    PrologVariable,
    UnparsedPrologTerm,
)


def check_atom(string, expected_type, expected_str):
    a = PrologAtom(string)
    assert_equal(a.name, string)
    assert_equal(a.atom_type, expected_type)
    assert_equal(str(a), expected_str)
    assert_equal(repr(a), 'PrologAtom(name={!r})'.format(string))


def test_prolog_atom_word_lower():
    check_atom('apple', 'word', 'apple')


def test_prolog_atom_word_upper():
    check_atom('aPPLE', 'word', 'aPPLE')
    check_atom('APPLE', 'quoted', "'APPLE'")
    check_atom('Apple', 'quoted', "'Apple'")


def test_prolog_atom_word_numbers():
    check_atom('a1234', 'word', 'a1234')
    check_atom('a6z3P', 'word', 'a6z3P')
    check_atom('1234', 'quoted', "'1234'")
    check_atom('123abc', 'quoted', "'123abc'")


def test_prolog_atom_word_underscore():
    check_atom('app_le', 'word', 'app_le')
    check_atom('apple_', 'word', 'apple_')
    check_atom('_apple', 'quoted', "'_apple'")


def test_prolog_atom_symbol_single():
    for symbol in r"+-*/\^><=':.?@#$&":
        yield check_atom, symbol, 'symbol', symbol


def test_prolog_atom_symbol_string():
    string = r"+-*/\^><=':.?@#$&+-*/\^><=':.?@#$&"
    check_atom(string, 'symbol', string)


def test_prolog_atom_symbol_mixed():
    check_atom('a*b', 'quoted', "'a*b'")
    check_atom('2<=5', 'quoted', "'2<=5'")


def test_prolog_atom_special():
    check_atom('[]', 'special', '[]')
    check_atom('{}', 'special', '{}')
    check_atom(';', 'special', ';')
    check_atom('!', 'special', '!')


def test_prolog_atom_quoted_spaces():
    check_atom('foo bar', 'quoted', "'foo bar'")


def test_prolog_atom_quoted_empty():
    check_atom('', 'quoted', "''")


def check_prolog_integer(num, num_int=None, num_string=None):
    if num_int is None:
        num_int = int(num)
    if num_string is None:
        num_string = str(num)
    pint = PrologInteger(num)
    assert_equal(str(pint), num_string)
    assert_equal(repr(pint), 'PrologInteger(value={!r})'.format(num_int))
    assert_equal(int(pint), num_int)


def test_prolog_integer():
    yield check_prolog_integer, 123
    yield check_prolog_integer, 0
    yield check_prolog_integer, -1
    yield check_prolog_integer, '123'
    yield check_prolog_integer, '0'
    yield check_prolog_integer, '-1'
    yield check_prolog_integer, 1.3, 1, '1'


def check_prolog_integer_invalid(value):
    with assert_raises(ValueError):
        PrologInteger(value)


def test_prolog_integer_invalid():
    yield check_prolog_integer_invalid, '1.3'
    yield check_prolog_integer_invalid, ''
    yield check_prolog_integer_invalid, 'asdf'
    yield check_prolog_integer_invalid, '0x41'


def check_prolog_float(num):
    num_float = float(num)
    num_string = str(num_float)
    pfloat = PrologFloat(num)
    assert_equal(str(pfloat), num_string)
    assert_equal(repr(pfloat), 'PrologFloat(value={!r})'.format(num_float))
    assert_equal(float(pfloat), num_float)


def test_prolog_float():
    yield check_prolog_float, 1.0
    yield check_prolog_float, 1
    yield check_prolog_float, -1
    yield check_prolog_float, '1.0'
    yield check_prolog_float, '1'
    yield check_prolog_float, '-1'
    yield check_prolog_float, '8E3'


def check_prolog_float_invalid(value):
    with assert_raises(ValueError):
        PrologFloat(value)


def test_prolog_float_invalid():
    yield check_prolog_float_invalid, ''
    yield check_prolog_float_invalid, 'asdf'
    yield check_prolog_float_invalid, '0x41'


def check_prolog_variable(name):
    pvar = PrologVariable(name)
    assert_equal(pvar.name, name)
    assert_equal(str(pvar), name)
    assert_equal(repr(pvar), 'PrologVariable(name={!r})'.format(name))


def test_prolog_variable():
    yield check_prolog_variable, 'X'
    yield check_prolog_variable, '_'
    yield check_prolog_variable, 'Var'
    yield check_prolog_variable, 'VAR'
    yield check_prolog_variable, 'CamelCase'
    yield check_prolog_variable, 'WITH_UNDERSCORES'
    yield check_prolog_variable, '_Var'
    yield check_prolog_variable, '_var'
    yield check_prolog_variable, '_1234'
    yield check_prolog_variable, 'A1234'
    yield check_prolog_variable, 'X_123_abc_XYZ'


def check_prolog_variable_invalid(name):
    with assert_raises(ValueError):
        PrologVariable(name)


def test_prolog_variable_invalid():
    yield check_prolog_variable_invalid, 'asdf'
    yield check_prolog_variable_invalid, 'aSDF'
    yield check_prolog_variable_invalid, '1234'
    yield check_prolog_variable_invalid, '_ _'
    yield check_prolog_variable_invalid, '_,abc'


def check_prolog_string(name, expected_str=None):
    if expected_str is None:
        expected_str = '"{!s}"'.format(name)
    pstr = PrologString(name)
    assert_equal(pstr.name, name)
    assert_equal(str(pstr), expected_str)
    assert_equal(repr(pstr), 'PrologString(name={!r})'.format(name))


def test_prolog_string():
    yield check_prolog_string, 'abc'
    yield check_prolog_string, ''
    yield check_prolog_string, 'X'
    yield check_prolog_string, '_'
    yield check_prolog_string, '1'
    yield check_prolog_string, ')'
    yield check_prolog_string, '+'
    yield check_prolog_string, '"', r'"\""'
    yield check_prolog_string, '\\', r'"\\"'


def test_prolog_compound_term_arity_0():
    pct = PrologCompoundTerm(name='foo', args=())
    assert_equal(pct.name, PrologAtom('foo'))
    assert_equal(pct.arity, 0)
    assert_equal(len(pct.args), 0)
    assert_equal(str(pct), 'foo()')
    assert_equal(repr(pct),
                 "PrologCompoundTerm(name=PrologAtom(name='foo'), args=[])")


def test_prolog_compound_term_name_requires_quotes_variable():
    pct = PrologCompoundTerm(name='X', args=())
    assert_equal(pct.name, PrologAtom('X'))
    assert_equal(str(pct), "'X'()")


def test_prolog_compound_term_name_requires_quotes_empty():
    pct = PrologCompoundTerm(name='', args=())
    assert_equal(pct.name, PrologAtom(''))
    assert_equal(str(pct), "''()")


def test_prolog_compound_term_arity_2_string_args():
    pct = PrologCompoundTerm(name='foo', args=('bar', '2'))
    assert_equal(pct.name, PrologAtom('foo'))
    assert_equal(pct.arity, 2)
    assert_equal(len(pct.args), 2)
    assert_equal(str(pct.args[0]), 'bar')
    assert_equal(str(pct.args[1]), '2')
    assert_is_instance(pct.args[0], PrologTerm)
    assert_is_instance(pct.args[1], PrologTerm)
    assert_in(str(pct), ('foo({}, {})'.format(str_bar, str_2)
                         for str_bar in ('bar', '(bar)')
                         for str_2 in ('2', '(2)')))


def test_prolog_compound_term_arity_3_term_args():
    arg_atom = PrologAtom('atom')
    arg_var = PrologVariable('Var')
    arg_int = PrologInteger(2)
    pct = PrologCompoundTerm(name='foo', args=(arg_atom, arg_var, arg_int))
    assert_equal(pct.name, PrologAtom('foo'))
    assert_equal(pct.arity, 3)
    assert_equal(len(pct.args), 3)
    assert_equal(pct.args[0], arg_atom)
    assert_equal(pct.args[1], arg_var)
    assert_equal(pct.args[2], arg_int)
    assert_equal(str(pct), 'foo(atom, Var, 2)')
    assert_equal(
        repr(pct),
        "PrologCompoundTerm(name={name!r}, args={args!r})".format(
            name=PrologAtom('foo'), args=[arg_atom, arg_var, arg_int]))


def test_prolog_compound_term_arity_2_nested():
    pct = PrologCompoundTerm(
        name='out',
        args=(PrologCompoundTerm('in1', args=(PrologVariable('X'),)),
              PrologCompoundTerm('in2', args=(PrologAtom('a'),))))
    assert_equal(pct.arity, 2)
    assert_equal(str(pct), 'out(in1(X), in2(a))')


def test_prolog_term_list_prepend():
    pct = PrologCompoundTerm(
        name='[|]',
        args=(PrologVariable('X'), PrologAtom('[]')))
    assert_equal(str(pct), '[X | []]')


def check_operator_format_on_atoms(operator, arity, expected_str):
    args = list(PrologAtom(chr(ord('a') + i)) for i in range(arity))
    assert_equal(str(PrologOperatorTerm(operator, args)),
                 expected_str)


def test_prolog_operator_term():
    yield check_operator_format_on_atoms, ',', 2, 'a , b'
    yield check_operator_format_on_atoms, '*', 2, 'a * b'
    yield check_operator_format_on_atoms, ':-', 1, ':- a'
    yield check_operator_format_on_atoms, '$', 1, r'$ a'
    yield check_operator_format_on_atoms, 'volatile', 1, 'volatile a'
    yield check_operator_format_on_atoms, '=', 2, 'a = b'


def test_prolog_operator_format_on_unparsed():
    assert_equal(
        str(PrologOperatorTerm(',', list(UnparsedPrologTerm(x) for x in 'ab'))),
        '(a) , (b)')


def test_prolog_operator_comma_in_compound_pred():
    pct = PrologCompoundTerm(
        name='foo',
        args=(PrologOperatorTerm(',', list(PrologAtom(x) for x in 'ab')),))
    assert_equal(str(pct), 'foo((a , b))')


def test_prolog_operator_precedence_arithmetic():
    pct = PrologOperatorTerm(
        '*',
        (PrologOperatorTerm('**', (PrologInteger(2), PrologInteger(3))),
         PrologOperatorTerm('+', (PrologInteger(4), PrologInteger(5)))))
    assert_equal(str(pct), '2 ** 3 * (4 + 5)')


def check_prolog_list(*args):
    expected_str = args[-1]
    elements = args[:-1]
    plist = PrologList(elements)
    assert_equal(len(plist), len(elements))
    assert_sequence_equal(list(iter(plist)), elements)
    for i in range(len(elements)):
        assert_equal(plist[i], elements[i])
    assert_equal(str(plist), expected_str)
    assert_equal(repr(plist), 'PrologList({})'.format(repr(list(elements))))


def test_prolog_list():
    yield check_prolog_list, '[]'
    yield check_prolog_list, PrologAtom('a'), '[a]'
    yield check_prolog_list, PrologAtom('a'), PrologAtom('b'), '[a, b]'
    yield (check_prolog_list,
           PrologList((PrologAtom('a'),)), PrologAtom('b'),
           '[[a], b]')
    yield (check_prolog_list,
           PrologCompoundTerm('foo', (PrologAtom('a'), PrologAtom('b'))),
           PrologVariable('X'),
           '[foo(a, b), X]')
    yield (check_prolog_list,
           PrologOperatorTerm('+', (PrologInteger(1), PrologFloat(2.3))),
           PrologOperatorTerm(',', (PrologAtom('a'), PrologAtom('b'))),
           '[1 + 2.3, (a , b)]')
    yield (check_prolog_list,
           PrologOperatorTerm(',', (PrologAtom('a'), PrologAtom('b'))),
           PrologOperatorTerm(',', (PrologAtom('c'), PrologAtom('d'))),
           '[(a , b), (c , d)]')


def check_unparsed_prolog_term(string):
    upt = UnparsedPrologTerm(string)
    assert_equal(upt.str, string)
    assert_equal(str(upt), string)
    assert_equal(repr(upt), 'UnparsedPrologTerm({!r})'.format(string))


def test_unparsed_prolog_term():
    yield check_unparsed_prolog_term, 'foo'
    yield check_unparsed_prolog_term, '1'
    yield check_unparsed_prolog_term, 'foo(bar, 2)'
    yield check_unparsed_prolog_term, 'X'


def check_unparsed_prolog_term_parse(string, *parsed):
    parsed_term = UnparsedPrologTerm(string).parse()
    if len(parsed) == 1:
        assert_equal(parsed_term, parsed[0])
    else:
        assert_in(parsed_term, parsed)


def test_unparsed_prolog_term_parse():
    yield check_unparsed_prolog_term_parse, 'a', PrologAtom('a')
    yield check_unparsed_prolog_term_parse, 'abc', PrologAtom('abc')
    yield check_unparsed_prolog_term_parse, 'Var', PrologVariable('Var')
    yield check_unparsed_prolog_term_parse, '_var', PrologVariable('_var')
    yield check_unparsed_prolog_term_parse, "'Atom'", PrologAtom('Atom')
    yield check_unparsed_prolog_term_parse, '5', PrologInteger(5)
    yield check_unparsed_prolog_term_parse, '-5', PrologInteger(-5)
    yield check_unparsed_prolog_term_parse, '0', PrologInteger(0)
    yield check_unparsed_prolog_term_parse, "'5'", PrologAtom('5')
    yield check_unparsed_prolog_term_parse, '1.2', PrologFloat(1.2)
    yield check_unparsed_prolog_term_parse, '-1.2', PrologFloat(-1.2)
    yield check_unparsed_prolog_term_parse, '*', PrologAtom('*')
    yield (check_unparsed_prolog_term_parse, 'foo()',
           PrologCompoundTerm('foo', ()))
    yield check_unparsed_prolog_term_parse, '"abc"', PrologString('abc')
    yield check_unparsed_prolog_term_parse, r'"a\"c"', PrologString('a"c')
    yield check_unparsed_prolog_term_parse, r'"a\\c"', PrologString('a\\c')
    yield (check_unparsed_prolog_term_parse, '[1, 1.2, a]',
           PrologList([PrologInteger(1), PrologFloat(1.2), PrologAtom('a')]),
           PrologCompoundTerm('[|]', args=(
               PrologInteger(1),
               PrologList([PrologFloat(1.2), PrologAtom('a')]))),
           PrologCompoundTerm('[|]', args=(
               PrologInteger(1),
               PrologCompoundTerm('[|]', args=(
                   PrologFloat(1.2),
                   PrologAtom('a'))))))


def check_prolog_term_make(term, prolog_term):
    assert_equal(PrologTerm.make(term), prolog_term)


def test_prolog_term_make():
    yield check_prolog_term_make, 'abc', UnparsedPrologTerm('abc')
    yield check_prolog_term_make, 'Abc', UnparsedPrologTerm('Abc')
    yield check_prolog_term_make, '_', UnparsedPrologTerm('_')
    yield check_prolog_term_make, '1', UnparsedPrologTerm('1')
    yield check_prolog_term_make, '1.2', UnparsedPrologTerm('1.2')
    yield check_prolog_term_make, 1, PrologInteger(1)
    yield check_prolog_term_make, 1.2, PrologFloat(1.2)
    yield (check_prolog_term_make, [1, 1.2, 'a'],
           PrologList([PrologInteger(1), PrologFloat(1.2),
                       UnparsedPrologTerm('a')]))


def check_prolog_term_make_compound_term(name, *args):
    expected = args[-1]
    term_args = args[:-1]
    assert_equal(PrologTerm.make_compound_term(name, term_args), expected)


def test_prolog_term_make_compound_term():
    yield (check_prolog_term_make_compound_term,
           'foo', PrologAtom('a'), PrologVariable('X'),
           PrologCompoundTerm('foo', (PrologAtom('a'), PrologVariable('X'))))
    yield (check_prolog_term_make_compound_term,
           '+', PrologInteger(1), PrologInteger(2),
           PrologOperatorTerm('+', (PrologInteger(1), PrologInteger(2))))


def check_prolog_term_and_(*args):
    expected_str = args[-1]
    terms = args[:-1]
    assert_equal(str(PrologTerm.and_(*terms)), expected_str)


def test_prolog_term_and_():
    yield check_prolog_term_and_, 'true'
    yield check_prolog_term_and_, PrologVariable('X'), 'X'
    yield check_prolog_term_and_, PrologAtom('a'), PrologVariable('X'), 'a , X'
    yield (check_prolog_term_and_,
           PrologAtom('a'), PrologVariable('X'), PrologAtom('b'),
           'a , X , b')
    yield (check_prolog_term_and_,
           PrologCompoundTerm('foo', (PrologAtom('a'), PrologAtom('b'))),
           PrologVariable('X'),
           'foo(a, b) , X')
    yield (check_prolog_term_and_,
           PrologOperatorTerm('+', (PrologInteger(1), PrologFloat(2.3))),
           PrologOperatorTerm(',', (PrologAtom('a'), PrologAtom('b'))),
           '1 + 2.3 , a , b')
    yield (check_prolog_term_and_,
           PrologOperatorTerm(',', (PrologAtom('a'), PrologAtom('b'))),
           PrologOperatorTerm(',', (PrologAtom('c'), PrologAtom('d'))),
           '(a , b) , c , d')

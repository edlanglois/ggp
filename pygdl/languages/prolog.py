"""Prolog"""
from collections import defaultdict, namedtuple
import os.path
import random
import string

import pyswip

from pygdl.paths import prolog_dir

_introspection_prolog_file = os.path.join(prolog_dir, 'introspection.pl')
_prolog_session = pyswip.Prolog()
_prolog_session.consult(_introspection_prolog_file)

PrologOperatorSpec = namedtuple('PrologOperatorSpec',
                                ('precedence', 'type'))


def _get_prolog_operators():
    operator_types = ('xf', 'yf', 'xfx', 'xfy', 'yfx', 'fy', 'fx')

    operators = defaultdict(dict)
    operator_query_results = \
        _prolog_session.query('current_op(Precedence, Type, Name)')
    for assignment in operator_query_results:
        type_ = assignment['Type']
        assert type_ in operator_types
        arity = len(type_) - 1
        operators[assignment['Name']][arity] = \
            PrologOperatorSpec(precedence=int(assignment['Precedence']),
                               type=type_)
    return dict(operators)
PrologOperators = _get_prolog_operators()


class PrologTerm(object):
    """Representation of a Prolog term."""

    @staticmethod
    def make_from_pyswip_term(pyswip_term, variable_map={}):
        """Create specified PrologTerm from pyswip term.

        The Prolog interpreter tends to forget the original names of variables
        and instead replaces them with names of the form _G####.
        variable_map can be provided to map these mangled names back to the
        original name.
        """
        if isinstance(pyswip_term, pyswip.Atom):
            return PrologAtom(name=str(pyswip_term))
        elif isinstance(pyswip_term, pyswip.Variable):
            name = str(pyswip_term)
            return PrologVariable(name=variable_map.get(name, name))
        elif isinstance(pyswip_term, pyswip.Functor):
            return PrologTerm.make_compound_term(
                name=str(pyswip_term.name),
                args=tuple(PrologTerm.make_from_pyswip_term(arg, variable_map)
                           for arg in pyswip_term.args))
        else:
            raise AssertionError(
                'Unexpected type: {}'.format(type(pyswip_term)))

    @staticmethod
    def make_compound_term(name, args):
        """Make a fully specific PrologCompoundTerm

        Returns a PrologOperatorTerm if possible.
        """
        try:
            operator_spec = PrologOperators[name][len(args)]
            return PrologOperatorTerm(name=name, args=args,
                                      operator_spec=operator_spec)
        except KeyError:
            return PrologCompoundTerm(name=name, args=args)

    @staticmethod
    def and_(*terms):
        """Return a PrologTerm that is true if all terms are true."""
        if not terms:
            return PrologTerm(name='true')

        terms = list(terms)
        combined_term = terms.pop()
        while terms:
            combined_term = PrologOperatorTerm(
                name=',', args=(terms.pop(), combined_term))
        return combined_term

    def str_precedence_less_equal(self, precedence):
        """String representation with precedence <= the given precedence."""
        assert precedence >= 0
        return self.str_zero_precedence()

    def str_zero_precedence(self):
        """String representation having zero precedence."""
        return '({!s})'.format(self)


class UnparsedPrologTerm(PrologTerm):
    def __init__(self, term):
        self.str = str(term)

    def __repr__(self):
        return '{}({})'.format(UnparsedPrologTerm.__name__,
                               self.str)

    def __str__(self):
        return self.str

    @staticmethod
    def _mangle_variable_name(variable_name):
        """Mangle a variable name to avoid name conflicts with other
        user-provided variables in an expression."""
        rand_low = 1000000
        rand_high = 10 * rand_low
        mangled_name = '_{prefix!s}_{name!s}_{randint!s}'.format(
            prefix=UnparsedPrologTerm.__name__,
            name=variable_name,
            randint=random.randint(rand_low, rand_high))
        return mangled_name

    def parse(self):
        """Return the corresponding ParsedPrologTerm."""
        term_var = self._mangle_variable_name('Term')
        term_type_var = self._mangle_variable_name('TermType')
        term_name_var = self._mangle_variable_name('Name')
        term_arguments_var = self._mangle_variable_name('Arguments')

        parse_variables = (
            term_var, term_type_var, term_name_var, term_arguments_var)

        results = _prolog_session.query(
            """{term_var} = ({term}),
            term_type({term_var}, {term_type_var}),
            (
                {term_type_var} = 'var' -> true;
                {term_type_var} = 'compound' ->
                    compound_name_arguments({term_var},
                                            {term_name_var},
                                            {term_arguments_var});
                functor({term_var}, {term_name_var}, _)
            ).
            """.format(
                term=self.str,
                term_var=term_var,
                term_type_var=term_type_var,
                term_name_var=term_name_var,
                term_arguments_var=term_arguments_var,
            ))
        assignment = next(results)
        results.close()

        variable_map = {
            str(var): name
            for name, var in assignment.items()
            if isinstance(var, pyswip.Variable) and name not in parse_variables}

        term_type = str(assignment[term_type_var])
        if term_type == 'var':
            raise AssertionError('Cannot handle variables yet.')

        term_name = str(assignment[term_name_var])
        if term_type == 'compound':
            return PrologTerm.make_compound_term(
                name=term_name,
                args=tuple(PrologTerm.make_from_pyswip_term(arg, variable_map)
                           for arg in
                           assignment[term_arguments_var]))
        if term_type == 'atom':
            return PrologAtom(term_name)
        elif term_type == 'int':
            return PrologInteger(term_name)
        elif term_type == 'float':
            return PrologFloat(term_name)
        elif term_type == 'string':
            raise AssertionError('Cannot handle strings yet.')
        else:
            raise AssertionError('Unexpected term type: {}'.format(term_type))


class ParsedPrologTerm(PrologTerm):
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.precedence = 0

    def str_precedence_less_equal(self, precedence):
        if self.precedence <= precedence:
            return str(self)
        else:
            return self.str_zero_precedence()

    def __repr__(self):
        return '{}(name={name!r}, args={args!r})'.format(
            self.__class__.__name__,
            name=self.name, args=self.args)


class PrologNonCompoundTerm(ParsedPrologTerm):
    def __init__(self, name):
        super().__init__(name=name, args=None)

    def __repr__(self):
        return '{}(name={name!r})'.format(
            self.__class__.__name__, name=self.name)

    def __str__(self):
        return str(self.name)


class PrologConstant(PrologNonCompoundTerm):
    pass


class PrologAtom(PrologConstant):
    word_atom_first_chars = string.ascii_lowercase
    word_atom_rest_chars = string.ascii_letters + string.digits + '_'
    symbol_atom_chars = r"+-*/\^><=':.?@#$&"
    special_atoms = ('[]', '{}', ';', '!')

    def __init__(self, name):
        super().__init__(name=name)
        if ((self.name[0] in self.word_atom_first_chars and
             all(c in self.word_atom_rest_chars for c in self.name[1:]))):
            self.atom_type = 'word'
        elif all(c in self.symbol_atom_chars for c in self.name):
            self.atom_type = 'symbol'
        elif self.name in self.special_atoms:
            self.atom_type = 'special'
        else:
            self.atom_type = 'quoted'

    def __str__(self):
        if self.atom_type == 'quoted':
            return "'{!s}'".format(self.name)
        else:
            return str(self.name)


class PrologNumber(PrologConstant):
    def __init__(self, value):
        super().__init__(name=str(value))
        self.value = value

    def __repr__(self):
        return '{}(value={value!s})'.format(
            self.__class_.__name__, value=self.value)


class PrologInteger(PrologNumber):
    def __init__(self, value):
        super().__init__(value=int(value))

    def __int__(self):
        return self.value


class PrologFloat(PrologNumber):
    def __init__(self, value):
        super().__init__(value=float(value))

    def __float__(self):
        return self.value


class PrologVariable(PrologNonCompoundTerm):
    def __init__(self, name):
        assert name[0].isupper() or name[0] == '_', \
            'Variable "{}" does not start with an upper case letter.'.format(
                name)
        super().__init__(name=name)


class PrologCompoundTerm(ParsedPrologTerm):
    _comma_operator_precedence = PrologOperators[','][2].precedence

    def __init__(self, name, args):
        super().__init__(name=name, args=args)
        self.arity = len(args)

    def __str__(self):
        args_string = ', '.join(
            arg.str_precedence_less_equal(self._comma_operator_precedence - 1)
            for arg in self.args)

        if self.name == '[]':
            return '[{}]'.format(args_string)
        elif self.name == '[|]':
            assert(len(self.args) == 2)
            return '[{!s} | {!s}]'.format(self.args[0], self.args[1])
        else:
            return '{name!s}({args!s})'.format(name=self.name, args=args_string)


class PrologOperatorTerm(PrologCompoundTerm):
    def __init__(self, name, args, operator_spec=None):
        super().__init__(name=name, args=args)
        if operator_spec is None:
            self.operator_spec = PrologOperators[name][self.arity]
        else:
            self.operator_spec = operator_spec
        self.precedence = self.operator_spec.precedence

    def __str__(self):
        args_iterator = iter(self.args)
        return ''.join(
            self._format_operator_character(char, args_iterator)
            for char in self.operator_spec.type)

    def _format_operator_character(self, char, args_iterator):
        if char == 'f':
            return str(self.name)
        if char == 'x':
            return next(args_iterator).str_precedence_less_equal(
                self.precedence - 1)
        if char == 'y':
            return next(args_iterator).str_precedence_less_equal(
                self.precedence)
        raise AssertionError('Unexpected operator character: {}'.format(char))


class PrologList(PrologCompoundTerm):
    """Provide a Sequence interface to a list prolog term."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_parsed:
            raise ValueError('Unparsed term: {!s}'.format(self))
        if self.name == '[|]':
            raise ValueError('Recursive type lists not supported.')
        if self.name != '[]':
            raise ValueError(
                'Term of type "{!s}" is not a list.'.format(self.name))

    def __len__(self):
        return len(self.args)

    def __iter__(self):
        return iter(self.args)

    def __getitem__(self, key):
        return self.args[key]

"""Translation between Prefix GDL and Prolog"""
from pygdl.languages import prefixgdl, prolog


def translate_prefix_gdl_to_prolog_terms(prefix_gdl_string):
    """Yield the prolog terms corresponding to prefix_gdl_string."""
    return _prefix_gdl_to_prolog_term.translate(prefix_gdl_string)


def translate_prolog_term_to_prefix_gdl(parsed_prolog_term):
    """Translate a ParsedPrologTerm to Prefix GDL."""
    if isinstance(parsed_prolog_term, prolog.PrologAtom):
        # str(Atom) may result in a quoted string
        # when the quotes should not appear in GDL
        return str(parsed_prolog_term.name)

    elif isinstance(parsed_prolog_term, prolog.PrologConstant):
        return str(parsed_prolog_term)

    elif isinstance(parsed_prolog_term, prolog.PrologVariable):
        name = str(parsed_prolog_term.name)
        return _prefix_gdl_variable_token + name[0].lower() + name[1:]

    elif isinstance(parsed_prolog_term, prolog.PrologCompoundTerm):
        name = parsed_prolog_term.name
        args = parsed_prolog_term.args
        if name == _prolog_rule_operator:
            name = _prefix_gdl_rule_operator

            # Prolog version of rule operator has arity 2 but GDL version is
            # variadic. Expand out a sequence of AND operators to create the
            # variadic call.
            assert len(args) == 2
            args = (args[0],) + _expand_prolog_conjunction(args[1])

        return '({name!s} {args!s})'.format(
            name=name,
            args=' '.join(translate_prolog_term_to_prefix_gdl(arg)
                          for arg in args))
    else:
        raise AssertionError('Unexpected prolog term type: {}'.format(
            type(parsed_prolog_term)))

_prolog_and_operator = ','
_prolog_rule_operator = ':-'
_prefix_gdl_rule_operator = '<='
_prefix_gdl_variable_token = '?'


class _PrefixGdlToPrologTerm(prefixgdl.PrefixGdlParser):
    """Translates prefix GDL to Prolog."""

    def __init__(self):
        super().__init__()
        self.variable.addParseAction(self._translate_variable)
        self.variable.addParseAction(self._prolog_variable)

        self.atom.addParseAction(self._prolog_atom)

        self.predicate_name.addParseAction(self._translate_predicate)

        self.compound_term.addParseAction(self._translate_compound_term)
        self.compound_term.addParseAction(self._prolog_compound_term)

    def translate(self, instring):
        return list(self.parse(instring))

    @staticmethod
    def _translate_variable(toks):
        return toks.variable[0].capitalize()

    @staticmethod
    def _prolog_variable(toks):
        return prolog.PrologVariable(toks.variable)

    @staticmethod
    def _prolog_atom(toks):
        return prolog.PrologAtom(toks.atom)

    @staticmethod
    def _translate_predicate(toks):
        if toks.name == _prefix_gdl_rule_operator:
            return _prolog_rule_operator

    @staticmethod
    def _translate_compound_term(toks):
        if toks.compound_term.name == _prolog_rule_operator:
            # The GDL version of this operator is variadic,
            # but the Prolog version has arity 2.
            toks.compound_term.arguments = (
                toks.compound_term.arguments[0],
                prolog.PrologTerm.and_(*(toks.compound_term.arguments[1:])))

    @staticmethod
    def _prolog_compound_term(toks):
        return prolog.PrologTerm.make_compound_term(
            name=str(toks.compound_term.name),
            args=tuple(toks.compound_term.arguments))

_prefix_gdl_to_prolog_term = _PrefixGdlToPrologTerm()


def _expand_prolog_conjunction(prolog_term):
    """Expand the conjuction represented by prolog_term

    Return a tuple of terms, where prolog_term represents a conjunction of these
    terms.
    """
    if ((isinstance(prolog_term, prolog.PrologCompoundTerm) and
         prolog_term.name == _prolog_and_operator)):
        assert prolog_term.arity == 2
        return (_expand_prolog_conjunction(prolog_term.args[0]) +
                _expand_prolog_conjunction(prolog_term.args[1]))
    else:
        return (prolog_term,)

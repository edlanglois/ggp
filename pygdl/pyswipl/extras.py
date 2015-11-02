from .prolog import Term, Functor, Atom


def consult(filename):
    """Consult a prolog file, importing its public predicates."""
    Term.from_cons_functor(
        Functor(Atom('consult'), 1),
        Term.from_atom_name(filename))()


and_functor = Functor(Atom(','), 2)


def make_and_term(*terms):
    """Combine multiple terms into a single term using the ``,`` functor.

    Args:
        *terms (prolog.Term) : Terms to combine.
    """
    if not terms:
        return Term.from_atom_chars('true')

    combined_term = terms[-1]
    for term in reversed(terms[:-1]):
        combined_term = Term.from_cons_functor(
            and_functor, term, combined_term)
    return combined_term


def make_list_term(*terms):
    """Combine multiple terms into a single list.

    Args:
        *terms (prolog.Term) : Terms to combine into a list.
    """
    list_term = Term.from_nil()

    for term in reversed(terms):
        list_term = Term.from_cons_list(term, list_term)
    return list_term

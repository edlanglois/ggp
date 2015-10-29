from .prolog import Term, Functor, Atom


def consult(filename):
    """Consult a prolog file, importing its public predicates."""
    Term.from_cons_functor(
        Functor(Atom('consult'), 1),
        Term.from_atom_name(filename))()


and_functor = Functor(Atom(','), 2)


def make_and_term(*terms):
    """Combined multiple terms into a single term using the ``,`` functor.

    Args:
        *terms (prolog.Term) : Terms to combine.
    """
    terms = list(terms)
    combined_term = terms.pop()
    while terms:
        combined_term = Term.from_cons_functor(
            and_functor, terms.pop(), combined_term)
    return combined_term

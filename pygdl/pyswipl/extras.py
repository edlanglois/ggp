from .prolog import Term, Functor, Atom


def consult(filename):
    """Consult a prolog file, importing its public predicates."""
    Term.from_cons_functor(
        Functor(Atom('consult'), 1),
        Term.from_atom_name(filename))()

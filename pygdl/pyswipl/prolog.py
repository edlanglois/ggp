from collections import namedtuple
from ctypes import (
    POINTER,
    byref,
    c_char,
    c_char_p,
    c_double,
    c_int,
    c_int64,
    c_size_t,
    c_void_p,
)

from .core import (
    BUF_DISCARDABLE,
    CVT_WRITE,
    PL_ATOM,
    PL_BLOB,
    PL_CHARS,
    PL_FLOAT,
    PL_FUNCTOR,
    PL_INTEGER,
    PL_LIST,
    PL_LIST_PAIR,
    PL_NIL,
    PL_POINTER,
    PL_Q_CATCH_EXCEPTION,
    PL_Q_NODEBUG,
    PL_STRING,
    PL_TERM,
    PL_VARIABLE,
    PL_atom_chars,
    PL_call,
    PL_call_predicate,
    PL_chars_to_term,
    PL_close_query,
    PL_cons_functor,
    PL_cons_functor_v,
    PL_cons_list,
    PL_context,
    PL_copy_term_ref,
    PL_exception,
    PL_functor_arity,
    PL_functor_name,
    PL_get_arg,
    PL_get_atom,
    PL_get_atom_nchars,
    PL_get_bool,
    PL_get_compound_name_arity,
    PL_get_float,
    PL_get_functor,
    PL_get_head,
    PL_get_int64,
    PL_get_list,
    PL_get_module,
    PL_get_name_arity,
    PL_get_nchars,
    PL_get_nil,
    PL_get_pointer,
    PL_get_string_chars,
    PL_get_tail,
    PL_is_acyclic,
    PL_is_atom,
    PL_is_atomic,
    PL_is_callable,
    PL_is_compound,
    PL_is_float,
    PL_is_functor,
    PL_is_ground,
    PL_is_integer,
    PL_is_list,
    PL_is_number,
    PL_is_pair,
    PL_is_string,
    PL_is_variable,
    PL_module_name,
    PL_new_atom,
    PL_new_functor,
    PL_new_module,
    PL_new_term_ref,
    PL_new_term_refs,
    PL_next_solution,
    PL_open_query,
    PL_pred,
    PL_predicate,
    PL_put_atom,
    PL_put_atom_nchars,
    PL_put_bool,
    PL_put_float,
    PL_put_functor,
    PL_put_int64,
    PL_put_list,
    PL_put_list_nchars,
    PL_put_nil,
    PL_put_pointer,
    PL_put_string_nchars,
    PL_put_term,
    PL_put_variable,
    PL_register_atom,
    PL_term_type,
    PL_unregister_atom,
    REP_UTF8,
    atom_t,
    functor_t,
    module_t,
    term_t,
)

_term_type_code_name = {
    PL_VARIABLE: 'variable',
    PL_ATOM: 'atom',
    PL_INTEGER: 'integer',
    PL_FLOAT: 'float',
    PL_STRING: 'string',
    PL_TERM: 'term',
    PL_NIL: 'nil',
    PL_BLOB: 'blob',
    PL_LIST_PAIR: 'list-pair',
    PL_FUNCTOR: 'functor',
    PL_LIST: 'list',
    PL_CHARS: 'chars',
    PL_POINTER: 'pointer',
}

__all__ = [
    'ActiveQuery',
    'Atom',
    'Functor',
    'Module',
    'Predicate',
    'PrologException',
    'Query',
    'Term',
    'TermList',
]


class PrologException(Exception):
    def __init__(self, exception_term):
        self.exception_term = exception_term

    def __str__(self):
        return "Prolog Exception:\n{!s}".format(self.exception_term)


class HandleWrapper(object):
    def __init__(self, handle):
        self._handle = handle

    @classmethod
    def _from_handle(cls, handle):
        """Initialize from an existing handle."""
        new_obj = cls.__new__(cls)
        HandleWrapper.__init__(new_obj, handle=handle)
        return new_obj


class Term(HandleWrapper):
    def __init__(self):
        """Initialize a new term. The term is initially a variable."""
        super(Term, self).__init__(handle=PL_new_term_ref())

    def __str__(self):
        """A Prolog string representing this term."""
        return self.get_chars()

    def __deepcopy__(self):
        """Creates a new Prolog term, copied from the old."""
        return self._from_handle(handle=PL_copy_term_ref(self._handle))

    def type(self):
        """Term type as a string.

        Returns one of the following strings:

            * ``variable``
            * ``atom``
            * ``integer``
            * ``float``
            * ``string``
            * ``term``
            * ``nil``
            * ``blob``
            * ``list-pair``
            * ``functor``
            * ``list``
            * ``chars``
            * ``pointer``
        """
        type_code = PL_term_type(self._handle)
        return _term_type_code_name[type_code]

    def is_acyclic(self):
        """True if this is an acyclic term."""
        return bool(PL_is_acyclic(self._handle))

    def is_atom(self):
        """True if this term is an atom."""
        return bool(PL_is_atom(self._handle))

    def is_atomic(self):
        """True if this term is atomic.

        A term is atomic if it is not variable or compound.
        """
        return bool(PL_is_atomic(self._handle))

    def is_callable(self):
        """True if this term is callable.

        A term is callable if it is compound or an atom.
        """
        return bool(PL_is_callable(self._handle))

    def is_compound(self):
        """True if this term is compound.

        A compound term is a functor with arguments.
        """
        return bool(PL_is_compound(self._handle))

    def is_float(self):
        """True if this term is a float."""
        return bool(PL_is_float(self._handle))

    def is_functor(self, functor):
        """True if this term is compound and its functor is `functor`.

        Args:
            functor (Functor): Check if this is the functor of `self`.
        """
        return bool(PL_is_functor(self._handle, functor._handle))

    def is_ground(self):
        """True if this term is a ground term.

        A ground term is a term that holds no free variables.
        """
        return bool(PL_is_ground(self._handle))

    def is_integer(self):
        """True if this term is an integer."""
        return bool(PL_is_integer(self._handle))

    def is_list(self):
        """True if this term is a list.

        A term is a list if it is:
            * a compound term using the list constructor (`is_pair`); or
            * the list terminator (`is_nil`).
        """
        return bool(PL_is_list(self._handle))

    def is_nil(self):
        """True if this term is the list terminator.

        The list terminator is the constant ``[]``.
        """
        self._require_success(
            PL_get_nil(self._handle))

    def is_number(self):
        """True if this term is an integer or float."""
        return bool(PL_is_number(self._handle))

    def is_pair(self):
        """True if this term is a compound term using the list constructor."""
        return bool(PL_is_pair(self._handle))

    def is_string(self):
        """True if this term is a string."""
        return bool(PL_is_string(self._handle))

    def is_variable(self):
        """True if this term is a variable."""
        return bool(PL_is_variable(self._handle))

    @staticmethod
    def _require_success(return_code):
        assert bool(return_code)

    @staticmethod
    def _require_success_expecting_type(return_code, *required_types):
        assert required_types
        if not bool(return_code):
            if len(required_types) == 1:
                type_str = required_types[0]
            elif len(required_types) == 2:
                type_str == '{} or {}'.format(*required_types)
            else:
                type_str = '{}, or {}'.format(
                    ', '.join(required_types[:-1],),
                    required_types[-1])

            raise TypeError('Term is not {a} {type}.'.format(
                a=('an' if type_str[0].lower() in 'aeiou' else 'a'),
                type=type_str))

    @staticmethod
    def _decode_ptr_len_string(ptr, length, encoding='utf8'):
        """Decode a string from a ctypes pointer and length."""
        return ptr[:length].decode(encoding)

    def get_atom(self):
        """An `Atom` object representing this term, if it is a prolog atom."""
        a = atom_t()
        self._require_success_expecting_type(
            PL_get_atom(self._handle, byref(a)),
            'atom')
        return Atom._from_handle(a.value)

    def get_atom_chars(self):
        """The value of this term as a string, if it is a prolog atom."""
        s = c_char_p()
        length = c_size_t()
        self._require_success_expecting_type(
            PL_get_atom_nchars(self._handle, byref(length), byref(s)),
            'atom')
        return self._decode_ptr_len_string(s, length)

    def get_string_chars(self):
        """The value of this term as a string, if it is a prolog string."""
        s = POINTER(c_char)()
        length = c_int()
        self._require_success_expecting_type(
            PL_get_string_chars(self._handle, byref(s), byref(length)),
            'string')
        return self._decode_ptr_len_string(s, length)

    def get_chars(self):
        """Representation of this term as a string in Prolog syntax."""
        s = POINTER(c_char)()
        length = c_size_t()
        self._require_success(
            PL_get_nchars(self._handle,
                          byref(length),
                          byref(s),
                          CVT_WRITE | BUF_DISCARDABLE | REP_UTF8))
        return self._decode_ptr_len_string(s, length, encoding='utf8')

    def get_integer(self):
        """The value of this term as an integer, if it is an integer or
        compatible float.
        """
        i = c_int64()
        self._require_success_expecting_type(
            PL_get_int64(self._handle, byref(i)),
            'integer', 'int-compatible float')
        return i.value

    def get_bool(self):
        """The value of this term as a boolean, if it is `true` or `false`."""
        i = c_int()
        self._require_success_expecting_type(
            PL_get_bool(self._handle, byref(i)),
            'boolean')
        return bool(i.value)

    def get_pointer(self):
        """The value of this term as an integer address, if it is a pointer."""
        p = c_void_p()
        self._require_success_expecting_type(
            PL_get_pointer(self._handle, byref(p)),
            'pointer')
        return p.value

    def get_float(self):
        """The value of this term as a float, if it is an integer or float."""
        f = c_double()
        self._require_success_expecting_type(
            PL_get_float(self._handle, byref(f)),
            'float', 'integer')
        return f.value

    def get_functor(self):
        """A `Functor` object representing this term, if it is a compound term
        or atom."""
        functor = functor_t()
        self._require_success_expecting_type(
            PL_get_functor(self._handle, byref(functor)),
            'compound term', 'atom')
        return Functor._from_handle(functor.value)

    NameArity = namedtuple('NameArity', ['name', 'arity'])

    def get_name_arity(self):
        """The name and arity of this term, if it is a compound term or an atom.

        Compound terms with arity 0 give the same result as an atom.
        To distingush them use `is_compound` and/or `get_compound_name_arity`.

        Returns:
            NameArity: namedtuple (name, arity)
        """

        name = atom_t()
        arity = c_int()
        self._require_success_expecting_type(
            PL_get_name_arity(self._handle, byref(name), byref(arity)),
            'compound term', 'atom')
        return self.NameArity(name=name.value, arity=arity.value)

    def get_compound_name_arity(self):
        """The name and arity of this term, if it is a compound term.

        The same as `get_name_arity` but fails for atoms.

        Returns:
            NameArity: Named tuple of name (`string`) and arity (`int`).
        """
        name = atom_t()
        arity = c_int()
        self._require_success_expecting_type(
            PL_get_compound_name_arity(self._handle, byref(name), byref(arity)),
            'compound term')
        return self.NameArity(name=name.value, arity=arity.value)

    def get_module(self):
        """A `Module` object corresponding to this term, if it is an atom."""
        module = module_t()
        self._require_success_expecting_type(
            PL_get_module(self._handle, byref(module)),
            'atom')
        return Module._from_handle(module.value)

    def get_arg(self, index):
        """An argument of this term, if this term is compound.

        Args:
            index (int): Index of the argument.
                Index is 0-based, unlike in Prolog.

        Returns:
            Term:

        Raises:
            AssertionError: If `index` is out of bounds or
                if this term is not compound.
        """
        t = term_t()
        self._require_success(
            PL_get_arg(index + 1, self._handle, t))
        return Term._from_handle(t.value)

    HeadTail = namedtuple('HeadTail', ['head', 'tail'])

    def get_list_head_tail(self):
        """Get the head and tail of the list represented by this term.

        Returns:
            HeadTail: Named tuple of head and tail, both `Term` objects.
        """
        head = term_t()
        tail = term_t()
        self._require_success_expecting_type(
            PL_get_list(self._handle, head, tail),
            'list')
        return self.HeadTail(head=Term._from_handle(head.value),
                             tail=Term._from_handle(tail.value))

    def get_list_head(self):
        """The head of the list represented by this term.

        Returns:
            Term:
        """
        head = term_t()
        self._require_success_expecting_type(
            PL_get_head(self._handle, head),
            'list')
        return Term._from_handle(head.value)

    def get_list_tail(self):
        """The tail of the list represented by this term.

        Returns:
            Term:
        """
        tail = term_t()
        self._require_success_expecting_type(
            PL_get_tail(self._handle, tail),
            'list')
        return Term._from_handle(tail.value)

    def get_nil(self):
        """Succeds if this term represents the list termination constant (nil).

        Raises:
            AssertionError: If this term does not represent nil.
        """
        self._require_success(
            PL_get_nil(self._handle))

    def put_variable(self):
        """Put a fresh variable in this term, resetting it to its initial state.
        """
        PL_put_variable(self._handle)

    def put_atom(self, atom):
        """Put an atom in this term.

        Args:
            atom (Atom): Atom to put in this term.
        """
        PL_put_atom(self._handle, atom._handle)

    def put_bool(self, val):
        """Put a boolean in this term.

        Puts either the atom ``true`` or the atom ``false``.
        """
        PL_put_bool(self._handle, int(bool(val)))

    def put_atom_name(self, atom_name):
        """Put an atom in this term, constructed from a string name.

        Args:
            atom_name (str): Name of the atom to put in this term.
        """
        encoded_atom_name = atom_name.encode()
        PL_put_atom_nchars(self._handle,
                           len(encoded_atom_name),
                           encoded_atom_name)

    def put_string(self, string):
        """Put a string in the term."""
        encoded_string = string.encode()
        self._require_success(
            PL_put_string_nchars(self._handle,
                                 len(encoded_string),
                                 encoded_string))

    def put_list_chars(self, bytes_):
        """Put a byte string in the term as a list of characters."""
        self._require_success(
            PL_put_list_nchars(self._handle,
                               len(bytes_),
                               bytes_))

    def put_integer(self, val):
        """Put an integer in the term."""
        self._require_success(
            PL_put_int64(self._handle, val))

    def put_pointer(self, address):
        """Put an integer address in the term."""
        self._require_success(
            PL_put_pointer(self._handle, address))

    def put_float(self, val):
        """Put a floating-point value in the term."""
        self._require_success(
            PL_put_float(self._handle, val))

    def put_functor(self, functor):
        """Put a compound term created from functor in this term.

        The arguments of the compound term are variables.
        To create a term with instantiated arguments, use `cons_functor`.
        """
        self._require_success(
            PL_put_functor(self._handle, functor._handle))

    def put_list(self):
        """Put a list pair in this term, whose head and tail are variables.

        Like `put_functor` but using the ``[|]`` functor.
        """
        self._require_success(
            PL_put_list(self._handle))

    def put_nil(self):
        """Put the list terminator constant in this term."""
        self._require_success(
            PL_put_nil(self._handle))

    def put_term(self, term):
        """Set this term to reference the new term."""
        PL_put_term(self._handle, term._handle)

    def put_parsed(self, string):
        """Parse `string` as Prolog as place the result in this term.

        Args:
            string (str): A term string in Prolog syntax.
                Optionally ends with a full-stop (.)

        Raises:
            PrologException: If the parse fails.
                The exception is also stored in this term.
        """
        success = PL_chars_to_term(string.encode(), term_t)
        if not success:
            raise PrologException(self)

    def cons_functor(self, functor, *args):
        """Set this term to a compound term created from `functor` and `args`.

        The length of `args` must be the same as the arity of `functor`.
        """
        self._require_success(
            PL_cons_functor(self._handle, functor._handle,
                            *[arg._handle for arg in args]))

    def cons_functor_v(self, functor, args):
        """Set this term to a compound term created from `functor` and args.

        Args:
            functor (Functor): Functor used to create the compound term.
            args (TermList)  : A term list of arguments.
        """
        self._require_success(
            PL_cons_functor_v(self._handle,
                              functor._handle,
                              args.head._handle))

    def cons_list(self, head, tail):
        """Set this term to a list constructed from head and tail."""
        self._require_success(
            PL_cons_list(self._handle, head._handle, tail._handle))

    def __call__(self, context_module=None):
        """Call term like once(term).

        Attempts to find an assignment of the variables in the term that
        makes the term true.

        Returns:
            bool: True if the call succeeded.
        """
        return bool(PL_call(self._handle,
                            _get_nullable_handle(context_module)))


class TermList(object):
    """A collection of term references.

    Required by `Term.cons_functor_v` and `Query`.
    """
    def __init__(self, length):
        self._length = length
        self.head = Term._from_handle(handle=PL_new_term_refs(length))

    def __len__(self):
        return self._length

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(self._length))]
        elif key == 0:
            return self.head
        elif key >= 1 and key <= self._length:
            return Term._from_handle(self.head._handle + key)
        else:
            raise IndexError()


class Atom(HandleWrapper):
    """Prolog Atom Interface"""
    def __init__(self, name):
        """Create a named atom."""
        super(Atom, self).__init__(handle=PL_new_atom(name))

    @classmethod
    def _from_handle(cls, handle):
        """Create an Atom object from an existing atom handle."""
        new_atom = super(Atom, cls)._from_handle(handle)
        PL_register_atom(new_atom._handle)
        return new_atom

    def get_name(self):
        """The atom's name as a string."""
        return PL_atom_chars(self._handle).decode()

    def __str__(self):
        return self.get_name()

    def __del__(self):
        PL_unregister_atom(self._handle)

    def __copy__(self):
        """A new `Atom` object pointing to the same atom."""
        return self._from_handle(self._handle)


class Functor(HandleWrapper):
    """Prolog Functor Interface"""
    def __init__(self, name, arity):
        """Create a functor.

        Args:
            name (Atom): Name of the functor.
                Either Atom object or string, the former is more efficient.
            arity (int): Arity of the functor.
        """
        try:
            name_handle = name._handle
        except AttributeError:
            name_handle = Atom(name=name)._handle

        super(Functor, self).__init__(
            handle=PL_new_functor(name_handle, arity))

    def get_name(self):
        """The functor's name as an `Atom` object."""
        return Atom._from_handle(PL_functor_name(self._handle))

    def get_arity(self):
        """The functor's arity as an integer."""
        return PL_functor_arity(self._handle)


class Module(HandleWrapper):
    """Prolog Module Interface"""
    def __init__(self, name):
        """Finds existing module or creates a new module with given name.

        Args:
            name (Atom): Name of the module.
        """
        super(Module, self).__init__(handle=PL_new_module(name._handle))

    @classmethod
    def current_context(cls):
        """Returns the current context module."""
        return cls._from_handle(PL_context())

    def get_name(self):
        """The name of the module as an `Atom` object."""
        return Atom._from_handle(PL_module_name(self._handle))


class Predicate(HandleWrapper):
    """Prolog Predicate Interface"""
    def __init__(self, functor, module=None):
        """Create a predicate from a functor.

        Args:
            functor (Functor): Functor used to create the predicate.
            module (Module)  : Module containing the functor.
                If ``None``, uses the current context module.
        """
        return super(Predicate, self).__init__(
            handle=PL_pred(functor._handle, _get_nullable_handle(module)))

    @classmethod
    def from_name_arity(cls, name, arity, module_name=None):
        """Create a predicate directly from Python's built-in types.

        Args:
            name (str)       : Name of functor used to create the predicate.
            arity (int)      : Arity of functor used to create the predicate.
            module_name (str): Name of module containing the functor.
                If ``None``, uses the current context module.
        """
        return cls._from_handle(handle=PL_predicate(name, arity, module_name))

    def __call__(self, arguments, goal_context_module=None):
        """Call predicate with arguments.

        Finds a binding for arguments that satisfies the predicate.
        Like Query but only finds the first solution.

        Args:
            arguments (TermList)        : List of arguments to this predicate.
            goal_context_module (Module): Context module of the goal.
                If ``None``, the current context module is used, or ``user`` if
                there is no context. This only matters for meta_predicates.

        Returns:
            bool: True if a binding for `arguments` was found.

        Raises:
            PrologException: If an exception was raised in Prolog.
        """
        success = bool(PL_call_predicate(
            _get_nullable_handle(goal_context_module),
            PL_Q_NODEBUG | PL_Q_CATCH_EXCEPTION,
            self._handle,
            arguments.head._handle))

        if not success:
            exception_term = PL_exception(self._handle)
            if exception_term:
                raise PrologException(Term._from_handle(exception_term))
        return success


class Query(object):
    """Prolog Query Context Manager."""
    def __init__(self, predicate, arguments, goal_context_module=None):
        """Prepare a query.

        A query conssists of a predicate (`predicate`) and a list of arguments
        (`arguments`). Each solution is an assignment to variables in
        `arguments` that satisfies the predicate.

        A query behaves statefully. The solutions must be read from `arguments`.

        Args:
            predicate (Predicate)       : Predicate to query.
            arguments (TermList)        : List of argument terms to `predicate`.
            goal_context_module (Module): Context module of the goal.
                If ``None``, the current context module is used, or ``user`` if
                there is no context. This only matters for meta_predicates.

        Note
        ----
        Only one query can be active at a time, but the query is not activated
        until `__enter__` is called.
        """
        self.predicate = predicate
        self.arguments = arguments
        self.goal_context_module = goal_context_module
        self.active_query = None

    def __enter__(self):
        self.active_query = ActiveQuery(
            predicate=self.predicate,
            arguments=self.arguments,
            goal_context_module=self.goal_context_module)
        return self.active_query

    def __exit__(self, type, value, traceback):
        self.active_query.close()


class ActiveQuery(HandleWrapper):
    """Interface to an active Prolog Query.

    Only one query can be active at a time.
    """
    def __init__(self, predicate, arguments, goal_context_module=None):
        """Create an active query. Arguments are the same as `Query.__init__`.
        """
        super(ActiveQuery, self).__init__(
            handle=PL_open_query(
                _get_nullable_handle(goal_context_module),
                PL_Q_NODEBUG | PL_Q_CATCH_EXCEPTION,
                self.predicate._handle,
                self.arguments.head._handle))

    def next_solution(self):
        """Find the next solution, updating `arguments`.

        Returns:
            bool: ``True`` if a solution was found, otherwise returns ``False``.

        Raises:
            PrologException: If an exception was raised in Prolog.
        """
        success = bool(PL_next_solution(self._handle))
        if not success:
            exception_term = PL_exception(self._handle)
            if exception_term:
                raise PrologException(Term._from_handle(exception_term))
        return success

    def close(self):
        """Close the query and destory all data and bindings associated with it.
        """
        PL_close_query(self._handle)


def _get_nullable_handle(handle_wrapper):
    """Return the handle of `handle_wrapper` or None"""
    if handle_wrapper is None:
        return None
    else:
        return handle_wrapper._handle
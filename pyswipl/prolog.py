from collections import namedtuple
from ctypes import (
    POINTER,
    byref,
    c_char,
    c_char_p,
    c_double,
    c_int,
    c_int64,
    c_long,
    c_void_p,
)

from pyswipl.core import (
    BUF_RING,
    CVT_ALL,
    CVT_WRITE,
    PL_ATOM,
    PL_CHARS,
    PL_FLOAT,
    PL_FUNCTOR,
    PL_INTEGER,
    PL_LIST,
    PL_POINTER,
    PL_STRING,
    PL_TERM,
    PL_VARIABLE,
    PL_atom_chars,
    PL_cons_functor,
    PL_cons_functor_v,
    PL_cons_list,
    PL_copy_term_ref,
    PL_functor_arity,
    PL_functor_name,
    PL_get_arg,
    PL_get_atom,
    PL_get_atom_chars,
    PL_get_bool,
    PL_get_chars,
    PL_get_compound_name_arity,
    PL_get_float,
    PL_get_functor,
    PL_get_head,
    PL_get_int64,
    PL_get_integer,
    PL_get_intptr,
    PL_get_list,
    PL_get_long,
    PL_get_module,
    PL_get_name_arity,
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
    PL_new_atom,
    PL_new_functor,
    PL_new_term_ref,
    PL_put_atom,
    PL_put_atom_chars,
    PL_put_bool,
    PL_put_float,
    PL_put_functor,
    PL_put_int64,
    PL_put_integer,
    PL_put_list,
    PL_put_nil,
    PL_put_pointer,
    PL_put_string_chars,
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
    PL_VARIABLE: 1,
    PL_ATOM: 2,
    PL_INTEGER: 3,
    PL_FLOAT: 4,
    PL_STRING: 5,
    PL_TERM: 6,
    PL_FUNCTOR: 10,
    PL_LIST: 11,
    PL_CHARS: 12,
    PL_POINTER: 13
}


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
        super(Term, self).__init__(handle=PL_new_term_ref())

    def __str__(self):
        return self.get_chars()

    def __deepcopy__(self):
        return self._from_handle(handle=PL_copy_term_ref(self._handle))

    def type(self):
        """Term type as a string."""
        type_code = PL_term_type(self._handle)
        return _term_type_code_name[type_code]

    def is_acyclic(self):
        return PL_is_acyclic(self._handle)

    def is_atom(self):
        return PL_is_atom(self._handle)

    def is_atomic(self):
        return PL_is_atomic(self._handle)

    def is_callable(self):
        return PL_is_callable(self._handle)

    def is_compound(self):
        return PL_is_compound(self._handle)

    def is_float(self):
        return PL_is_float(self._handle)

    def is_functor(self):
        return PL_is_functor(self._handle)

    def is_ground(self):
        return PL_is_ground(self._handle)

    def is_integer(self):
        return PL_is_integer(self._handle)

    def is_list(self):
        return PL_is_list(self._handle)

    def is_number(self):
        return PL_is_number(self._handle)

    def is_pair(self):
        return PL_is_pair(self._handle)

    def is_string(self):
        return PL_is_string(self._handle)

    def is_variable(self):
        return PL_is_variable(self._handle)

    @staticmethod
    def _require_success(return_code):
        assert return_code

    def get_atom(self):
        a = atom_t()
        self._require_success(PL_get_atom(self._handle, byref(a)))
        return Atom._from_handle(a.value)

    def get_atom_chars(self):
        s = c_char_p()
        self._require_success(PL_get_atom_chars(self._handle, byref(s)))
        return s.value.decode()

    def get_string_chars(self):
        s = POINTER(c_char)()
        len_ = c_int()
        self._require_success(PL_get_string_chars(
            self._handle, byref(s), byref(len_)))
        return s[:len_].decode()

    def get_chars(self):
        s = c_char_p()
        self._require_success(
            PL_get_chars(self._handle,
                         byref(s),
                         CVT_ALL | CVT_WRITE | BUF_RING | REP_UTF8))
        return s.value.decode('utf8')

    def get_integer(self):
        i = c_int()
        self._require_success(PL_get_integer(self._handle, byref(i)))
        return i.value

    def get_long(self):
        i = c_long()
        self._require_success(PL_get_long(self._handle, byref(i)))
        return i.value

    def get_intptr(self):
        p = c_void_p()
        self._require_success(PL_get_intptr(self._handle, byref(p)))
        return p.value

    def get_int64(self):
        i = c_int64()
        self._require_success(PL_get_int64(self._handle, byref(i)))
        return i.value

    def get_bool(self):
        i = c_int()
        self._require_success(PL_get_bool(self._handle, byref(i)))
        return bool(i.value)

    def get_pointer(self):
        p = c_void_p()
        self._require_success(PL_get_pointer(self._handle, byref(p)))
        return p.value

    def get_float(self):
        f = c_double()
        self._require_success(PL_get_float(self._handle, byref(f)))
        return f.value

    def get_functor(self):
        functor = functor_t()
        self._require_success(PL_get_functor(self._handle, byref(functor)))
        return Functor._from_handle(functor.value)

    NameArity = namedtuple('NameArity', ['name', 'arity'])

    def get_name_arity(self):
        name = atom_t()
        arity = c_int()
        self._require_success(PL_get_name_arity(
            self._handle, byref(name), byref(arity)))
        return self.NameArity(name=name.value, arity=arity.value)

    def get_compound_name_arity(self):
        name = atom_t()
        arity = c_int()
        self._require_success(PL_get_compound_name_arity(
            self._handle, byref(name), byref(arity)))
        return self.NameArity(name=name.value, arity=arity.value)

    def get_module(self):
        module = module_t()
        self._require_success(PL_get_module(self._handle, byref(module)))
        return Module._from_handle(module.value)

    def get_arg(self, index):
        t = term_t()
        self._require_success(PL_get_arg(index, self._handle, t))
        return Term._from_handle(t.value)

    HeadTail = namedtuple('HeadTail', ['head', 'tail'])

    def get_list_head_tail(self):
        head = term_t()
        tail = term_t()
        self._require_success(PL_get_list(self._handle, head, tail))
        return self.HeadTail(head=Term._from_handle(head.value),
                             tail=Term._from_handle(tail.value))

    def get_list_head(self):
        head = term_t()
        self._require_success(PL_get_head(self._handle, head))
        return Term._from_handle(head.value)

    def get_list_tail(self):
        tail = term_t()
        self._require_success(PL_get_tail(self._handle, tail))
        return Term._from_handle(tail.value)

    def get_nil(self):
        self._require_success(PL_get_nil(self._handle))

    def put_variable(self):
        PL_put_variable(self._handle)

    def put_atom(self, atom):
        PL_put_atom(self._handle, atom._handle)

    def put_bool(self, val):
        PL_put_bool(self._handle, int(val))

    def put_atom_chars(self, chars):
        PL_put_atom_chars(self._handle, chars)

    def put_string_chars(self, chars):
        PL_put_string_chars(self._handle, chars)

    def put_integer(self, val):
        PL_put_integer(self._handle, val)

    def put_int64(self, val):
        PL_put_int64(self._handle, val)

    def put_pointer(self, address):
        PL_put_pointer(self._handle, address)

    def put_float(self, val):
        PL_put_float(self._handle, val)

    def put_functor(self, functor):
        PL_put_functor(self._handle, functor._handle)

    def put_list(self):
        PL_put_list(self._handle)

    def put_nil(self):
        PL_put_nil(self._handle)

    def put_term(self, term):
        PL_put_term(self._handle, term._handle)

    def cons_functor(self, functor, *args):
        PL_cons_functor(self._handle, functor._handle,
                        *[arg._handle for arg in args])

    def cons_functor_v(self, functor, a0):
        PL_cons_functor_v(self._handle, functor._handle, a0._handle)

    def cons_list(self, head, tail):
        PL_cons_list(self._handle, head._handle, tail._handle)


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
        return self._from_handle(self._handle)

    def __deepcopy__(self):
        return Atom(name=self.get_name())


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
        """The functor's name as an Atom object."""
        return Atom._from_handle(PL_functor_name(self._handle))

    def get_arity(self):
        """The functor's arity as an integer."""
        return PL_functor_arity(self._handle)


class Module(HandleWrapper):
    """Prolog Module Interface"""
    pass

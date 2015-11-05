from pygdl.pyswipl.prolog import *

f = Functor(Atom('foo'), 1)
print(str(f), repr(f))
t = Term.from_functor(f)
print(str(t), repr(t))
t0 = t[0]
print(str(t0))
print(repr(t0))

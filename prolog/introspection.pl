% Introspection into prolog terms.

:- module(
	introspection,
	[
		% Get the type of a term
		%
		% term_type(Term, Type)
		%
		% Possible types are:
		% var, atom, integer, float, string, compound
		term_type/2
	]
).

% IsTrue = true if Pred is satisfiable, otherwise IsTrue = false
is_true(Pred, IsTrue) :- (Pred -> IsTrue = true; IsTrue = false).

term_type(Term, Type) :-
	var(Term) -> Type = 'var';
	atom(Term) -> Type = 'atom';
	integer(Term) -> Type = 'integer';
	float(Term) -> Type = 'float';
	string(Term) -> Type = 'string';
	compound(Term) -> Type = 'compound'.

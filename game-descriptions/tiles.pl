distinct(X, Y) :- dif(X, Y).
or(A, _) :- A.
or(_, B) :- B.

gamerule(role(robot)).
gamerule(base(cell(M, N, T)) :- (index(M), index(N), tile(T))).
gamerule(base(step(1))).
gamerule(base(step(N)) :- (successor(_M, N))).
gamerule(index(1)).
gamerule(index(2)).
gamerule(tile(1)).
gamerule(tile(2)).
gamerule(tile(3)).
gamerule(tile(b)).
gamerule(input(robot, left)).
gamerule(input(robot, right)).
gamerule(input(robot, up)).
gamerule(input(robot, down)).
gamerule(init(cell(1, 1, b))).
gamerule(init(cell(1, 2, 3))).
gamerule(init(cell(2, 1, 2))).
gamerule(init(cell(2, 2, 1))).
gamerule(init(step(1))).
gamerule(legal(robot, left) :- (true(cell(_M, 2, b)))).
gamerule(legal(robot, right) :- (true(cell(_M, 1, b)))).
gamerule(legal(robot, up) :- (true(cell(2, _N, b)))).
gamerule(legal(robot, down) :- (true(cell(1, _N, b)))).
gamerule(next(cell(1, N, b)) :- (does(robot, up), true(cell(2, N, b)))).
gamerule(next(cell(2, N, b)) :- (does(robot, down), true(cell(1, N, b)))).
gamerule(next(cell(M, 1, b)) :- (does(robot, left), true(cell(M, 2, b)))).
gamerule(next(cell(M, 2, b)) :- (does(robot, right), true(cell(M, 1, b)))).
gamerule(next(cell(2, N, X)) :- (does(robot, up), true(cell(2, N, b)), true(cell(1, N, X)))).
gamerule(next(cell(1, N, X)) :- (does(robot, down), true(cell(1, N, b)), true(cell(2, N, X)))).
gamerule(next(cell(M, 2, X)) :- (does(robot, left), true(cell(M, 2, b)), true(cell(M, 1, X)))).
gamerule(next(cell(M, 1, X)) :- (does(robot, right), true(cell(M, 1, b)), true(cell(M, 2, X)))).
gamerule(next(cell(M, N, W)) :- (does(robot, up), true(cell(_X, Y, b)), true(cell(M, N, W)), distinct(Y, N))).
gamerule(next(cell(M, N, W)) :- (does(robot, down), true(cell(_X, Y, b)), true(cell(M, N, W)), distinct(Y, N))).
gamerule(next(cell(M, N, W)) :- (does(robot, left), true(cell(X, _Y, b)), true(cell(M, N, W)), distinct(X, M))).
gamerule(next(cell(M, N, W)) :- (does(robot, right), true(cell(X, _Y, b)), true(cell(M, N, W)), distinct(X, M))).
gamerule(next(step(N)) :- (true(step(M)), successor(M, N))).
gamerule(goal(robot, 100) :- (true(cell(1, 1, 1)), true(cell(1, 2, 2)), true(cell(2, 1, 3)))).
gamerule(goal(robot, 0) :- (not(true(cell(1, 1, 1))))).
gamerule(goal(robot, 0) :- (not(true(cell(1, 2, 2))))).
gamerule(goal(robot, 0) :- (not(true(cell(2, 1, 3))))).
gamerule(terminal :- (true(step(7)))).
gamerule(successor(1, 2)).
gamerule(successor(2, 3)).
gamerule(successor(3, 4)).
gamerule(successor(4, 5)).
gamerule(successor(5, 6)).
gamerule(successor(6, 7)).

get_requires_state(Term) :-
	get_requires_state(Term, []).

get_requires_state(true/1, _).
get_requires_state(Name/Arity, Visited) :-
	not(member(Name/Arity, Visited)),
	gamerule(Term :- _),
	functor(Term, Name, Arity),
	gamerule(Term :- Body),
	contains_state(Body, [Name/Arity | Visited]).

contains_state(Term, Visited) :-
	not(var(Term)),
	functor(Term, Name, Arity),
	get_requires_state(Name/Arity, Visited).
contains_state(Term, Visited) :-
	compound(Term),
	Term =.. [_ | Args],
	member(ArgTerm, Args),
	contains_state(ArgTerm, Visited).

:- dynamic(requires_state/1).
:- retractall(requires_state(_)).
:- setof(Predicate, get_requires_state(Predicate), Predicates),
   forall(member(Pred, Predicates), assertz(requires_state(Pred))).
:- compile_predicates([requires_state/1]).

stateify(Term, _State, _CurDoesList, StateifiedTerm) :-
	var(Term),
	!,
	StateifiedTerm = Term.

stateify(does(Role, Action), _State, CurDoesList, StateifiedTerm) :-
	!,
	StateifiedTerm = member(does(Role, Action), CurDoesList).

stateify(Term, State, CurDoesList, StateifiedTerm) :-
	Term =.. [Name | Args],
	stateify_list(Args, State, CurDoesList, StateifiedArgs),
	StateifiedOriginalTerm =.. [Name | StateifiedArgs],
	functor(Term, Name, Arity),
	(requires_state(Name/Arity) ->
		(StateifiedTerm = state(State, StateifiedOriginalTerm, CurDoesList));
		(StateifiedTerm = StateifiedOriginalTerm)).

stateify_list([], _, _, []).
stateify_list([First | Rest], State, CurDoesList, StateifiedList) :-
	stateify(First, State, CurDoesList, StateifiedFirst),
	StateifiedList = [StateifiedFirst | StateifiedRest],
	stateify_list(Rest, State, CurDoesList, StateifiedRest).

% Transformed Game Description
:- dynamic(state/3).
:- retractall(state(_, _, _)).
state([], true(X), _) :-
	base(X),
	init(X).
state([CurDoesList | RestState], true(X), _) :-
	validate_doeslist(CurDoesList, RestState),
	state(RestState, next(X), CurDoesList).
:- forall((gamerule(X), stateify(X, _State, _CurDoesList, Y)),
          (print(Y), print('\n'), assertz(Y))).
:- findall(Name/Arity,
           (gamerule(Head :- _),
            functor(Head, Name, Arity),
            not(requires_state(Name/Arity))),
           List),
   list_to_set(List, Set),
   compile_predicates(Set).
:- compile_predicates([state/3]).

state(State, Fact) :- state(State, Fact, []).

ordered_doeslist([], _State, []).
ordered_doeslist([Role | Roles], State, [Does | RestDoes]) :-
	Does = does(Role, Action),
	state(State, legal(Role, Action)),
	ordered_doeslist(Roles, State, RestDoes).

% Efficient version when DoesList is given
validate_doeslist(DoesList, State) :-
	ground(DoesList),
	!,
	setof(Role, role(Role), Roles),
	length(Roles, NumRoles),
	length(DoesList, NumRoles),
	forall(member(Role, Roles),
	       (member(does(Role, Action), DoesList),
	        state(State, legal(Role, Action)))).

validate_doeslist(DoesList, State) :-
	setof(Role, role(Role), Roles),
	length(Roles, NumRoles),
	length(DoesList, NumRoles),
	ordered_doeslist(Roles, State, OrderedDoesList),
	permutation(DoesList, OrderedDoesList).

%validate_doeslist(DoesList, State) :-
%	setof(Role, role(Role), Roles),
%	length(

%	findall(Role, member(does(Role, _), DoesList), DoesRoles),
%	msort(Roles, SortedRoles),
%	msort(DoesRoles, SortedDoesRoles),
%	SortedRoles = SortedDoesRoles,
%	forall(member(does(Role, Action), DoesList),
%	       state(State, legal(Role, Action))).

%--% Directly apply game rules
%--:- forall(gamerule(X), assert(X)).
%--% Compile the asserted game rules
%--:- findall(Name/Arity,
%--           ((gamerule(Head :- _); (gamerule(Head), Head \= (_ :- _))),
%--            functor(Head, Name, Arity)),
%--           Bag),
%--   list_to_set(Bag, Set),
%--   compile_predicates(Set).
%--
%--% Utility
%--
%--% Apply Func to each term. Combine results using Combine
%--recurse_terms((A, B), Func, Combine) :-
%--	!,
%--	call(Combine,
%--	     recurse_terms(A, Func, Combine),
%--	     recurse_terms(B, Func, Combine)).
%--recurse_terms((A; B), Func, Combine) :-
%--	!,
%--	call(Combine,
%--	     recurse_terms(A, Func, Combine),
%--	     recurse_terms(B, Func, Combine)).
%--recurse_terms((A -> B), Func, Combine) :-
%--	!,
%--	call(Combine,
%--	     recurse_terms(A, Func, Combine),
%--	     recurse_terms(B, Func, Combine)).
%--recurse_terms((A :- B), Func, Combine) :-
%--	!,
%--	call(Combine,
%--	     recurse_terms(A, Func, Combine),
%--	     recurse_terms(B, Func, Combine)).
%--recurse_terms(not(A), Func, Combine) :-
%--	!,
%--	recurse_terms(A, Func, Combine).
%--recurse_terms(Term, Func, _Combine) :- call(Func, Term).
%--
%--any_term(Terms, Func) :- recurse_terms(Terms, Func, ;).
%--all_terms(Terms, Func) :- recurse_terms(Terms, Func, ,).
%--
%--% Set up game description
%--% TODO: Memoize
%--
%--contains_state(Terms) :- any_term(Terms, get_requires_state_term).
%--get_requires_state_term(true(_)).
%--get_requires_state_term(Term) :-
%--	gamerule(Term :- Body),
%--	contains_state(Body).
%--
%--:- dynamic(requires_state).
%--:- findall(Name/Arity,
%--           (get_requires_state_term(Term),
%--            functor(Term, Name, Arity)),
%--           Bag),
%--   list_to_set(Bag, Set),
%--   forall(member(NameArity, Set), assert(requires_state(NameArity))).
%--:- compile_predicates([requires_state/1]).
%--
%--state([], true(X), _CurDoesList) :-
%--	base(X),
%--	init(X).
%--state([CurDoesList | RestState], true(Fact), _CurDoesList) :-
%--	validate_doeslist(CurDoesList, RestState),
%--	gamerule(base(Fact)),
%--	gamerule(next(Fact) :- Body),
%--	stateify(Body, RestState, CurDoesList).
%--state(State, Term, CurDoesList) :-
%--	Term \= true(_),
%--	functor(Term, Name, Arity),
%--	requires_state(Name/Arity),
%--	gamerule(Term :- Body),
%--	stateify(Body, State, CurDoesList).
%--
%--state(State, Term) :- state(State, Term, []).
%--
%--stateify(does(Role, Action), _State, CurDoesList) :-
%--	!,
%--	member(does(Role, Action), CurDoesList).
%--
%--stateify(Term, State, CurDoesList) :-
%--	functor(Term, Name, Arity),
%--	requires_state(Name/Arity),
%--	!,
%--	state(State, Term, CurDoesList).
%--
%--stateify(Term, State, CurDoesList) :-
%--	compound(Term),
%--	!,
%--	Term =.. [Name | Args0],
%--	% TODO: Don't wrap if not necessary.
%--	% Don't want foo(1, 1) -> foo(statify(1), statify(1))
%--	stateify_list(Args0, State, CurDoesList, Args1),
%--	Term1 =.. [Name | Args1],
%--	Term1.
%--
%--stateify(Term, _State, _CurDoesList) :- Term.
%--
%--stateify_list([], _State, _CurDoesList, []).
%--stateify_list([Front | Rest], State, CurDoesList, [stateify(Front, State, CurDoesList) | Out]) :-
%--	stateify_list(Rest, State, CurDoesList, Out).
%--
%--validate_doeslist(DoesList, State) :-
%--	setof(Role, role(Role), Roles),
%--	findall(Role, member(does(Role, _), DoesList), DoesRoles),
%--	msort(Roles, SortedRoles),
%--	msort(DoesRoles, SortedDoesRoles),
%--	SortedRoles = SortedDoesRoles,
%--	forall(member(does(Role, Action), DoesList),
%--	       state(State, legal(Role, Action))).
%--
%--

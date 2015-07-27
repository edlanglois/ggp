% Tic-Tac-Toe
% -----------

% Components
role(white).
role(black).

base(cell(M, N, x)) :- index(M), index(N).
base(cell(M, N, o)) :- index(M), index(N).
base(cell(M, N, b)) :- index(M), index(N).
base(control(white)).
base(control(black)).

input(R, mark(M, N)) :- role(R), index(M), index(N).
input(R, noop) :- role(R).

index(1).
index(2).
index(3).

% Init
init(cell(1, 1, b)).
init(cell(1, 2, b)).
init(cell(1, 3, b)).
init(cell(2, 1, b)).
init(cell(2, 2, b)).
init(cell(2, 3, b)).
init(cell(3, 1, b)).
init(cell(3, 2, b)).
init(cell(3, 3, b)).
init(control(white)).

% Legal
legal(W, mark(X, Y)) :- true(cell(X, Y, b)), true(control(W)).
legal(white, noop) :- true(control(black)).
legal(black, noop) :- true(control(white)).

% Next
next(cell(M, N, x)) :- does(white, mark(M, N)), true(cell(M, N, b)).
next(cell(M, N, o)) :- does(black, mark(M, N)), true(cell(M, N, b)).
next(cell(M, N, W)) :- true(cell(M, N, W)), distinct(W, b).
next(cell(M, N, b)) :- does(_, mark(J, _)), true(cell(M, N, b)), distinct(M, J).
next(cell(M, N, b)) :- does(_, mark(_, K)), true(cell(M, N, b)), distinct(N, K).
next(control(white)) :- true(control(black)).
next(control(black)) :- true(control(white)).

row(M, X) :- true(cell(M, 1, X)), true(cell(M, 2, X)), true(cell(M, 3, X)).
column(N, X) :- true(cell(1, N, X)), true(cell(2, N, X)), true(cell(3, N, X)).
diagonal(X) :- true(cell(1, 1, X)), true(cell(2, 2, X)), true(cell(3, 3, X)).
diagonal(X) :- true(cell(1, 3, X)), true(cell(2, 2, X)), true(cell(3, 1, X)).

line(X) :- row(_M, X).
line(X) :- column(_M, X).
line(X) :- diagonal(X).

open :- true(cell(_M, _N, b)).

% Goal
goal(white, 100) :- line(x), not(line(o)).
goal(white, 50) :- not(line(x)), not(line(o)).
goal(white, 0) :- not(line(x)), line(o).
goal(black, 100) :- not(line(x)), line(o).
goal(black, 50) :- not(line(x)), not(line(x)).
goal(black, 0) :- line(x), not(line(o)).

% Terminal
terminal :- line(x).
terminal :- line(o).
terminal :- not(open).

% Game Manager
distinct(X, Y) :- dif(X, Y).

:- dynamic turn/1, does/2, true/1, nexttrue/1.

update :-
	forall(role(Role), (
		findall(Move, does(Role, Move), MoveList), length(MoveList, L), L == 1,
		does(Role, Move), legal(Role, Move))),
	forall(base(Fact), (not(next(Fact)); assert(nexttrue(Fact)))),
	format('1~n~n~n2', []),
	retractall(true(_)),
	format('3~n~n~n4', []),
	forall(nexttrue(Fact), assert(true(Fact))),
	retractall(nexttrue(_)),
	turn(T),
	succ(T, U),
	assert(turn(U)),
	retract(turn(T)).

setmove(Role, Move) :-
	role(Role),
	legal(Role, Move),
	retractall(does(Role, _)),
	assert(does(Role, Move)).

% Initialize game
:- retractall(turn(_)).
turn(1).
:- retractall(true(_)).
:- forall(init(Fact), assert(true(Fact))).

% Play game
:- setmove(white, mark(2, 2)).
:- setmove(black, noop).

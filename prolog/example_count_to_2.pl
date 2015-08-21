% Count-to-2 game. ggp_state example.
:- use_module(ggp_state).

gamerule(role(counter)).
gamerule(base(count(1))).
gamerule(base(count(2))).
gamerule(init(count(1))).
gamerule(legal(counter, countto(2)) :- true(count(1))).
gamerule(next(count(2)) :- (true(count(1)), does(counter, countto(2)))).
gamerule(terminal :- true(count(2))).
gamerule(goal(counter, 100) :- true(count(2))).
gamerule(goal(counter, 0) :- (true(count(X)), distinct(X, 2))).

:- bagof(Rule, gamerule(Rule), Rules),
   create_game(count_to_2, Rules).

:- game_truth_state(count_to_2, InitialTruthState),
   setof(Role, game_state(count_to_2, InitialTruthState, role(Role)), Roles),
   print(Roles), print('\n').
% [counter]

:- game_truth_state(count_to_2, InitialTruthState),
   setof(does(Role, Action),
         game_state(count_to_2, InitialTruthState, legal(Role, Action)),
         LegalMoves),
   print(LegalMoves), print('\n').
% [does(counter, countto(2))]

:- move_history_game_state(count_to_2, [], goal(counter, Utility)),
   print(Utility), print('\n').
% 0

:- prepare_moves(count_to_2, [does(counter, countto(2))], PreparedMoves),
   game_truth_state(count_to_2, [PreparedMoves], TruthState),
   game_state(count_to_2, TruthState, goal(counter, Utility)),
   print(Utility), print('\n'),
% 100
   game_state(count_to_2, TruthState, terminal).
% true

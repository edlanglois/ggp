% General Game Playing - Game State Engine
%
% Mainpulate games specified with Game Description Language (GDL)
% http://logic.stanford.edu/classes/cs227/2013/readings/gdl_spec.pdf

:- module(
	ggp_state,
	[
		% Create a game from the given list of rules.
		%
		% create_game(GameId, Rules)
		%
		% GameId is used to identify a particular game.
		% Multiple games may be loaded under different IDs.
		% If a game has already been created under GameId, it is overwritten.
		%
		% Rules is a list of rules describing the game.
		% The game definition symantics follows GDL.
		% However, the rules must be given using valid Prolog syntax, rather than
		% the Knowledge Interchange Format (KIF) syntax used with GDL.
		create_game/2,

		% Game State
		%
		% game_state(GameId, TruthState, Fact)
		% game_state(GameId, TruthState, Moves, Fact)
		%
		% True if Fact is a true fact about the game loaded under GameId in
		% particular TruthState. If Moves is provided, it is the list of
		% moves to be performed this turn.
		%
		% Use truth_history and final_truth_state to generate a TruthState from
		% a list of move sets.
		% Use prepare_moves and/or legal_prepared_moves to generate Moves.
		%
		% At minimum (if the game was created from valid GDL rules), the following
		% GDL keyword terms will unify with Fact when TruthState is valid:
		%
		%     true(X)             - X is true in the current game state
		%     goal(Role, Utility) - Utility of the current state for Role
		%                           Utility is an integer in [0, 100].
		%     legal(Role, Action) - Action is a legal move for Role in the
		%                           current state.
		%     terminal            - The current state is terminal.
		%
		% these additional terms do not depend on the game state and will unify
		% the same regardless of the value of TruthState or Moves
		%
		%     role(Role)          - Role is a role in the game.
		%     init(X)             - X is true in the initial game state.
		%     base(X)             - X is a property of a game state.
		%                           true(X) implies base(X) for any game state.
		%                           (Only exists in some GDL versions)
		%     input(Role, Action) - Action can be a legal move for Role in a game
		%                           state. legal(Role, Action) implies
		%                           input(Role, Action) for any game state.
		%                           (Only exists in some GDL versions)
		%
		% and if Moves is provided:
		%
		%     does(Role, Action)  - If does(Role, Action) is in Moves
		%     next(X)             - If X is true in the next game state
		game_state/3,
		game_state/4,

		% Create a list of truth states corresponding to a move list.
		%
		% truth_history(GameId, MoveHistory, TruthHistory)
		% truth_history(GameId, MoveHistory, KnownTruthHistory, TruthHistory)
		%
		% MoveHistory is a list of Moves (e.g. each produced by prepare_moves)
		% describing the moves taken from the start of the game.
		%
		% TruthHistory is the list (Moves, TruthState) where Moves corresponds to
		% MoveHistory and TruthState is the truth state resulting from applying all
		% moves in MoveHistory up to and including Moves. Moves = start for the
		% first move.
		%
		% Use final_truth_state to extract the most recent TruthState from
		% TruthHistory.
		%
		% KnownTruthHistory is an alternate TruthHistory that has already been
		% computed. It does not have to correspond exactly to MoveHistory but its
		% values will be used as much as possible (safely) where re-computation can
		% be avoid.
		% e.g. If only the last move has been changed, only the final TruthState
		% will be computed.
		truth_history/3,
		truth_history/4,

		% Get the final TruthState from a TruthHistory
		%
		% final_truth_state(TruthHistory, TruthState).
		final_truth_state/2,

		% The TruthState resulting from a MoveHistory
		%
		% game_truth_state(GameId, TruthState)
		% game_truth_state(GameId, MoveHistory, TruthState)
		%
		% Equivalent to:
		%   truth_history(GameId, MoveHistory, TruthHistory),
		%   final_truth_state(TruthHistory, TruthState).
		%
		% When MoveHistory is not provided, TruthState is the initial truth state
		% for the game.
		game_truth_state/2,
		game_truth_state/3,

		% Prepare list of moves for use in game_state and TruthHistory
		%
		% prepare_moves(GameId, Moves, PreparedMoves)
		%
		% Moves is a list of does(Role, Action) pairs where each game Role has
		% exactly one action. PreparedMoves is that same list in the order
		% expected by game_state.
		prepare_moves/3,

		% Validate a list of moves.
		%
		% legal_prepared_moves(GameId, TruthState, PreparedMoves)
		%
		% Ensures that PreparedMoves is a legal set of moves for GameId in
		% TruthState.
		legal_prepared_moves/3,

		% Game state associated with a MoveHistory
		%
		% move_history_game_state(GameId, MoveHistory, Fact)
		%
		% Equivalent to:
		%   truth_history(GameId, MoveHistory, TruthHistory),
		%   final_truth_state(TruthHistory, TruthState),
		%   game_state(GameId, TruthState, Fact).
		%
		% This is just a convenience function. If making many game state queries, it
		% is more efficient to generate the TruthState once and use with each
		% game_state query.
		move_history_game_state/3
	]
).

create_game(GameId, Rules) :-
	stateify_game_rules(Rules, GameId, StateifiedRules),
	assert_game_rules(GameId, StateifiedRules).

game_state(_GameId, TruthState, _Moves, true(X)) :-
	member(X, TruthState).
game_state(_GameId, _Truth, Moves, does(Role, Action)) :-
	member(does(Role, Action), Moves).
game_state(GameId, TruthState, Moves, Fact) :-
	game_state_dynamic(GameId, TruthState, Moves, Fact).

game_state(GameId, TruthState, Fact) :-
	game_state(GameId, TruthState, none, Fact).

final_truth_state([(_, TruthState) | _], TruthState).

game_truth_state(GameId, TruthState) :-
	game_truth_state(GameId, [], TruthState).
game_truth_state(GameId, MoveHistory, TruthState) :-
	truth_history(GameId, MoveHistory, TruthHistory),
	final_truth_state(TruthHistory, TruthState).

move_history_game_state(GameId, MoveHistory, Fact) :-
	truth_history(GameId, MoveHistory, TruthHistory),
	final_truth_state(TruthHistory, TruthState),
	game_state(GameId, TruthState, Fact).

game_predicates(Rules, GamePredicates) :-
	findall(PredID,
	        (member(Rule, Rules), game_rule_predicate(Rule, PredID)),
	        PredicateList),
	list_to_set([true/1, does/2 | PredicateList], GamePredicates).

game_rule_predicate((Head :- _), PredicateID) :-
	functor(Head, Name, Arity),
	PredicateID = Name/Arity.
game_rule_predicate(Rule, PredicateID) :-
	not(Rule = (_ :- _)),
	functor(Rule, Name, Arity),
	PredicateID = Name/Arity.

prepare_moves(GameId, Moves, PreparedMoves) :-
	simple_validate_moves(GameId, PreparedMoves),
	permutation(Moves, PreparedMoves).

legal_prepared_moves(GameId, TruthState, PreparedMoves) :-
	simple_validate_moves(GameId, TruthState, PreparedMoves),
	all_moves_legal(GameId, TruthState, PreparedMoves).

% Re-write the given term so that all instances of PredicatesToWrap are
% wrapped in WrapperHead(WrapperArgs..., OriginalTerm)
% where WrapperInfo = (WrapperHead, WrapperArgs)
wrap_term(Term, _PredicatesToWrap, _WrapperInfo, WrappedTerm) :-
	var(Term),
	WrappedTerm = Term.

wrap_term(Term, PredicatesToWrap, WrapperInfo, WrappedTerm) :-
	nonvar(Term),
	wrap_term_top_rest(Term, PredicatesToWrap, WrapperInfo, WrapperInfo, WrappedTerm).

% Like wrap_term but wraps the top-level term using TopWrapperInfo and all
% lower-level terms using RestWrapperInfo.
wrap_term_top_rest(Term, PredicatesToWrap, TopWrapperInfo, RestWrapperInfo, WrappedTerm) :-
	Term =.. [Name | Args],
	wrap_term_list(Args, PredicatesToWrap, RestWrapperInfo, WrappedArgs),
	WrappedOriginalTerm =.. [Name | WrappedArgs],
	functor(Term, Name, Arity),
	(member(Name/Arity, PredicatesToWrap) -> (
		(WrapperName, WrapperArgs) = TopWrapperInfo,
		append(WrapperArgs, [WrappedOriginalTerm], CompleteWrapperArgs),
		WrappedTerm =.. [WrapperName | CompleteWrapperArgs]
	) ; (
		WrappedTerm = WrappedOriginalTerm
	)).

wrap_term_list([], _, _, []).
wrap_term_list([First | Rest],
               PredicatesToWrap,
               WrapperInfo,
               [WrappedFirst | WrappedRest]) :-
	wrap_term(First, PredicatesToWrap, WrapperInfo, WrappedFirst),
	wrap_term_list(Rest, PredicatesToWrap, WrapperInfo, WrappedRest).

% Wrap game rule, possibly differentiating the top-level term in the head
wrap_game_rule(Rule, PredicatesToWrap, WrapperInfo, WrappedRule) :-
	wrap_term(Rule, PredicatesToWrap, WrapperInfo, WrappedRule).

wrap_game_rule((Head :- Body),
               PredicatesToWrap,
               TopWrapperInfo,
               RestWrapperInfo,
               (WrappedHead :- WrappedBody)) :-
	wrap_term_top_rest(Head, PredicatesToWrap, TopWrapperInfo, RestWrapperInfo, WrappedHead),
	wrap_term(Body, PredicatesToWrap, RestWrapperInfo, WrappedBody).
wrap_game_rule(Rule,
               PredicatesToWrap,
               TopWrapperInfo,
               RestWrapperInfo,
               WrappedRule) :-
	not(Rule = (_ :- _)),
	wrap_term_top_rest(Rule, PredicatesToWrap, TopWrapperInfo, RestWrapperInfo, WrappedRule).

wrap_game_rules([], _, _, []).
wrap_game_rules([Rule | Rules], PredicatesToWrap, WrapperInfo, [WrappedRule | WrappedRules]) :-
	wrap_game_rule(Rule, PredicatesToWrap, WrapperInfo, WrappedRule),
	wrap_game_rules(Rules, PredicatesToWrap, WrapperInfo, WrappedRules).

wrap_game_rules([], _, _, _, []).
wrap_game_rules([Rule | Rules],
                PredicatesToWrap,
                TopWrapperInfo,
                RestWrapperInfo,
                [WrappedRule | WrappedRules]) :-
	wrap_game_rule(Rule, PredicatesToWrap, TopWrapperInfo, RestWrapperInfo, WrappedRule),
	wrap_game_rules(Rules, PredicatesToWrap, TopWrapperInfo, RestWrapperInfo, WrappedRules).

stateify_game_rules(Rules, GameId, StateifiedRules) :-
	game_predicates(Rules, GamePredicates),
	StateArgs = [GameId, _Truth, _Moves],
	wrap_game_rules(Rules,
	                GamePredicates,
	                (game_state_dynamic, StateArgs),
	                (game_state, StateArgs),
	                StateifiedRules).

assert_game_rules(GameId, Rules) :-
	(current_predicate(game_state_dynamic/4) -> true; dynamic(game_state_dynamic/4)),
	dynamic(game_state_dynamic_backup/4),
	copy_predicate_clauses(game_state_dynamic/4, game_state_dynamic_backup/4),
	retractall(game_state_dynamic_backup(GameId, _, _, _)),
	abolish(game_state_dynamic/4),
	dynamic(game_state_dynamic/4),
	copy_predicate_clauses(game_state_dynamic_backup/4, game_state_dynamic/4),
	abolish(game_state_dynamic_backup/4),
	forall(
		member(Rule, Rules),
		(
			((Rule = (Head :- _)) -> (
				functor(Head, game_state_dynamic, 4)
			) ; (
				functor(Rule, game_state_dynamic, 4)
			)),
			assertz(Rule)
		)),
	compile_predicates([game_state_dynamic/4]).

% Build a list of the truth states of the game according to a list of moves.
truth_history(GameId, [], [(start, TruthState)]) :-
	setof(
		Fact,
		(
			game_state(GameId, _, _, base(Fact)),
			game_state(GameId, _, _, init(Fact))
		),
		TruthState).

truth_history(GameId,
              [Moves | MoveHistory],
              [(Moves, TruthState) | TruthHistory]) :-
	simple_validate_moves(GameId, Moves),
	truth_history(GameId, MoveHistory, TruthHistory),
	current_truth(GameId, false, TruthHistory, Moves, _, (Moves, TruthState), _).

% Truth history where an alternate cached history is provided.
% The cache is used as much as possible.
truth_history(GameId, MoveHistory, CachedTruthHistory, TruthHistory) :-
	truth_history(GameId, MoveHistory, CachedTruthHistory, TruthHistory, _).
truth_history(GameId,
              [Moves | MoveHistory],
              [CachedMovesTruth | CachedTruthHistory],
              [MovesTruth | TruthHistory],
              CacheMatches) :-
	simple_validate_moves(GameId, Moves),
	truth_history(GameId,
                MoveHistory,
                CachedTruthHistory,
                TruthHistory,
                RestCacheMatches),
	current_truth(GameId,
                RestCacheMatches,
                TruthHistory,
                Moves,
                CachedMovesTruth,
                MovesTruth,
                CacheMatches).

current_truth(_GameId,
              true,
              _TruthHistory,
              Moves,
              (Moves, TruthState),
              (Moves, TruthState),
              true) :-
	ground(TruthState).
current_truth(GameId,
              _RestCacheMatches,
              TruthHistory,
              Moves,
              CachedMovesTruth,
              (Moves, TruthState),
              false) :-
	not(current_truth(GameId,
	                  true,
	                  TruthHistory,
	                  Moves,
	                  CachedMovesTruth,
	                  (Moves, TruthState),
		                true)),
	[(_, PrevTruth) | _] = TruthHistory,
	all_moves_legal(GameId, PrevTruth, Moves),
	setof(X, game_state(GameId, PrevTruth, Moves, next(X)), TruthState).

simple_validate_moves(GameId, Moves) :-
	setof(Role, game_state(GameId, _, _, role(Role)), Roles),
	simple_validate_ordered_moves(Roles, Moves).

simple_validate_ordered_moves([], []).
simple_validate_ordered_moves([Role | Roles], [Move | Moves]) :-
	Move = does(Role, _),
	simple_validate_ordered_moves(Roles, Moves).

all_moves_legal(_GameId, _Truth, []).
all_moves_legal(GameId, TruthState, [does(Role, Action) | Moves]) :-
	game_state(GameId, TruthState, legal(Role, Action)),
	all_moves_legal(GameId, TruthState, Moves).

% Predicates to be used by the game rules
distinct(X, Y) :- dif(X, Y).
or(A, _) :- A.
or(_, B) :- B.

import logging
import os.path

from pygdl.pyswipl.extras import (
    and_functor, consult, make_and_term, make_list_term)
from pygdl.pyswipl.prolog import (
    Atom,
    Functor,
    Module,
    Predicate,
    Query,
    Term,
    TermList,
    TermRecord as ActionRecord,
)
from pygdl.languages.prolog import PrologList
from pygdl.paths import prolog_dir

__all__ = [
    'GeneralGameManager',
    'GeneralGame',
    'GeneralGameState',
    'ActionRecord',
]

logger = logging.getLogger(__name__)

# Read in game state rules
consult(os.path.join(prolog_dir, 'ggp_state.pl'))


class GeneralGameManager(object):
    """Manage game descriptions using SWI-Prolog"""

    _ggp_state = Module(Atom('ggp_state'))
    _game_id_predicate = Predicate(functor=Functor(Atom('game_id'), 1),
                                   module=_ggp_state)
    _create_game_predicate = Predicate(functor=Functor(Atom('create_game'), 2),
                                       module=_ggp_state)
    _game_state_functor = Functor(Atom('game_state'), 3)
    _game_state_predicate = Predicate(functor=_game_state_functor,
                                      module=_ggp_state)
    _and_predicate = Predicate(functor=and_functor)

    def __init__(self):
        super().__init__()

        self._logger = logging.getLogger(__name__ + self.__class__.__name__)

    def game_exists(self, game_id):
        """Return true if a game with id game_id has been created."""
        args = TermList(1)
        args[0].put_atom_name(game_id)
        return self._game_id_predicate(args)

    def create_game(self, game_id, rules):
        """Create a game with the given game_id and rules set."""
        args = TermList(2)
        args[0].put_atom_name(game_id)
        args[1].put_parsed(str(PrologList(rules)))
        self._create_game_predicate(args, check=True)

    def game(self, game_id):
        """Get a GeneralGame object representing game_id"""
        return GeneralGame(self, game_id)

    def role_object(self, role):
        """Convert a role string to a role object usable in GGP methods."""
        return Atom(role)

    @staticmethod
    def _game_state_term_single(game_id, game_state, query):
        """Construct a term representing a fact about a game state.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            query      (prolog.Term) : Fact about the current game state.

        Returns:
            prolog.Term:
        """
        return Term.from_cons_functor(GeneralGameManager._game_state_functor,
                                      game_id, game_state, query)

    @staticmethod
    def _game_state_term(game_id, game_state, *queries):
        """Construct a term representing one or more facts about a game state.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            *queries   (prolog.Term) : Facts about the current game state.

        Returns:
            prolog.Term:
        """
        assert queries
        if len(queries) == 1:
            return GeneralGameManager._game_state_term_single(
                game_id, game_state, queries[0])
        else:
            return make_and_term(*(
                GeneralGameManager._game_state_term_single(
                    game_id, game_state, query)
                for query in queries))

    @staticmethod
    def _game_state_query_single(game_id, game_state, query):
        """Construct a query of a game state fact.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            query      (prolog.Term) : Fact about the current game state.

        Returns:
            prolog.Query:
        """
        args = TermList(3)
        args[0].put_term(game_id)
        args[1].put_term(game_state)
        args[2].put_term(query)
        return Query(predicate=GeneralGameManager._game_state_predicate,
                     arguments=args)

    @staticmethod
    def _game_state_query(game_id, game_state, *queries):
        """Construct a query of one or more game state facts.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            *queries   (prolog.Term) : Facts about the current game state.

        Returns:
            prolog.Query:
        """
        assert queries
        if len(queries) == 1:
            return GeneralGameManager._game_state_query_single(
                game_id, game_state, queries[0])
        else:
            args = TermList(2)
            args[0].put_term(GeneralGameManager._game_state_term_single(
                game_id, game_state, queries[0]))
            args[1].put_term(GeneralGameManager._game_state_term(
                game_id, game_state, *queries[1:]))
            return Query(predicate=GeneralGameManager._and_predicate,
                         arguments=args)


class GeneralGame(object):
    """A general game."""

    _empty_game_state_term = Term.from_atom_name('none')
    _role_functor = Functor(Atom('role'), 1)
    _input_functor = Functor(Atom('input'), 2)
    _base_functor = Functor(Atom('base'), 1)

    def __init__(self, game_manager, game_id):
        self.game_manager = game_manager
        self.game_id_atom = game_id
        self.game_id = Term.from_atom_name(game_id)

    def __eq__(self, other):
        return (self.game_manager == other.game_manager and
                self.game_id_atom == other.game_id_atom)

    def initial_state(self):
        """Return the initial state of the game as a GeneralGameState"""
        return GeneralGameState(self)

    def roles(self):
        """An iterator of the game roles (each a PrologTerm)"""
        role_variable = Term()
        role_query_term = Term.from_cons_functor(
            self._role_functor, role_variable)

        with self._stateless_query(role_query_term) as q:
            while q.next_solution():
                yield role_variable.get_atom()

    def num_roles(self):
        """The number of roles in the game."""
        return len(set(self.roles()))

    def all_actions(self, role, persistent):
        """All possible actions for `role` in this game.

        This does not represent the legal actions in some state.
        It is an iterator of all actions which may be available to role at some
        time in the game.

        If `persistent` is ``False`` then each yielded term is valid only
        until the term after it is yielded. If `persistent` is ``True``, then
        `TermRecord`s are yielded instead of `Term`s.
        """
        action_variable = Term()
        input_query_term = Term.from_cons_functor(
            self._input_functor, Term.from_atom(role), action_variable)

        with self._stateless_query(input_query_term) as q:
            yield from q.term_assignments(action_variable,
                                          persistent=persistent)

    def base_terms(self, persistent):
        """A list of the terms which define the game state."""
        base_variable = Term()
        base_query_term = Term.from_cons_functor(
            self._base_functor, base_variable)

        with self._stateless_query(base_query_term) as q:
            yield from q.term_assignments(base_variable,
                                          persistent=persistent)

    def max_utility(self):
        """Maximum utility achievable by any player."""
        return 100

    def min_utility(self):
        """Minimum utility achievable by any player."""
        return 0

    def role_object(self, role):
        return self.game_manager.role_object(role)

    def action_object(self, action):
        return Term.from_parsed(action)

    def _stateless_query_term(self, *queries):
        return self._stateful_query_term(self._empty_game_state_term, *queries)

    def _stateful_query_term(self, state, *queries):
        return self.game_manager._game_state_term(self.game_id, state, *queries)

    def _stateless_query(self, *queries):
        return self._stateful_query(self._empty_game_state_term, *queries)

    def _stateful_query(self, state, *queries):
        return self.game_manager._game_state_query(
            self.game_id, state, *queries)


class GeneralGameState(object):
    """A general game state."""

    _terminal_atom = Atom('terminal')

    _base_functor = GeneralGame._base_functor
    _does_functor = Functor(Atom('does'), 2)
    _eq_functor = Functor(Atom('='), 2)
    _final_truth_state_functor = Functor(Atom('final_truth_state'), 2)
    _goal_functor = Functor(Atom('goal'), 2)
    _legal_functor = Functor(Atom('legal'), 2)
    _prepare_moves_functor = Functor(Atom('prepare_moves'), 3)
    _true_functor = Functor(Atom('true'), 1)
    _truth_history_3_functor = Functor(Atom('truth_history'), 3)
    _truth_history_4_functor = Functor(Atom('truth_history'), 4)

    _final_truth_state_predicate = Predicate(
        functor=_final_truth_state_functor,
        module=GeneralGameManager._ggp_state)
    _length_predicate = Predicate(functor=Functor(Atom('length'), 2))
    _truth_history_3_predicate = Predicate(
        functor=_truth_history_3_functor,
        module=GeneralGameManager._ggp_state)
    _truth_history_4_predicate = Predicate(
        functor=_truth_history_4_functor,
        module=GeneralGameManager._ggp_state)

    def __init__(self, game,
                 move_history=None,
                 truth_history=None,
                 truth_state=None):
        self.game = game

        if move_history is None:
            self.move_history = Term.from_nil()
        else:
            self.move_history = move_history

        if truth_history is None:
            args = TermList(3)
            args[0].put_term(self.game_id())
            args[1].put_term(self.move_history)
            self._truth_history_3_predicate(args, check=True)
            self.truth_history = Term.from_term(args[2])
        else:
            self.truth_history = truth_history

        if truth_state is None:
            args = TermList(2)
            args[0].put_term(self.truth_history)
            self._final_truth_state_predicate(args, check=True)
            self.truth_state = Term.from_term(args[1])
        else:
            self.truth_state = truth_state

    def __eq__(self, other):
        return (self.game == other.game and
                self.truth_state == other.truth_state)

    def turn_number(self):
        """The current turn number."""
        args = TermList(2)
        args[0].put_term(self.move_history)
        self._length_predicate(args, check=True)
        return int(args[1])

    def utility(self, role):
        """The utility of the current state for the given role."""
        utility = Term()
        utility_query = Term.from_cons_functor(
            self._goal_functor, Term.from_atom(role), utility)
        self._query_term(utility_query)(check=True)
        if utility.is_atom():
            return int(str(utility))
        else:
            return int(utility)

    def legal_actions(self, role, persistent):
        """An iterator of legal actions for role in the current state."""
        action = Term()
        action_query = Term.from_cons_functor(
            self._legal_functor, Term.from_atom(role), action)
        with self._query(action_query) as q:
            yield from q.term_assignments(action, persistent=persistent)

    def state_terms(self, persistent):
        """Iterator of the base terms that are true for this state."""
        state_term = Term()
        base_term_query = Term.from_cons_functor(
            self._base_functor, state_term)
        true_term_query = Term.from_cons_functor(
            self._true_functor, state_term)
        with self._query(base_term_query, true_term_query) as q:
            yield from q.term_assignments(state_term, persistent=persistent)

    def is_terminal(self):
        """True if the current game state is terminal."""
        return self._query_term(Term.from_atom(self._terminal_atom))()

    def apply_moves(self, moves):
        """A new game state representing the game after moves are applied.

        Returns a new state, this state is unchanged.
        `moves` is a dictionary of role => action.
        """
        moves_term = make_list_term(*[
            Term.from_cons_functor(self._does_functor,
                                   Term.from_atom(role), action)
            for (role, action) in moves.items()])

        # prepare_moves(game_id, moves_term, PreparedMoves)
        prepared_moves = Term()
        prepare_moves_query = Term.from_cons_functor(
            self._prepare_moves_functor,
            self.game_id(), moves_term, prepared_moves)

        # NewMoveHistory = [PreparedMoves | old_move_history]
        new_move_history = Term()
        move_history_query = Term.from_cons_functor(
            self._eq_functor, new_move_history, Term.from_cons_list(
                prepared_moves, self.move_history))

        # truth_history(game_id, NewMoveHistory, old_truth_history,
        #               NewTruthHistory)
        new_truth_history = Term()
        truth_history_query = Term.from_cons_functor(
            self._truth_history_4_functor,
            self.game_id(), new_move_history, self.truth_history,
            new_truth_history)

        # final_truth_state(NewTruthHistory, NewTruthState)
        new_truth_state = Term()
        truth_state_query = Term.from_cons_functor(
            self._final_truth_state_functor,
            new_truth_history, new_truth_state)

        make_and_term(prepare_moves_query, move_history_query,
                      truth_history_query, truth_state_query)(check=True)

        return GeneralGameState(
            game=self.game,
            move_history=new_move_history,
            truth_history=new_truth_history,
            truth_state=new_truth_state,
        )

    def game_id(self):
        return self.game.game_id

    def role_object(self, role):
        return self.game.role_object(role)

    def _query_term(self, *queries):
        return self.game._stateful_query_term(self.truth_state, *queries)

    def _query(self, *queries):
        return self.game._stateful_query(self.truth_state, *queries)

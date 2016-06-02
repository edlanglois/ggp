import logging
import os.path

from swilite import (
    Atom,
    Frame,
    Functor,
    Module,
    Predicate,
    PrologCallFailed,
    Query,
    Term,
    TermList,
    TermRecord,
)
from ggp.paths import prolog_dir
from ggp.languages.prefixgdl import (
    prefix_gdl_statement_to_prolog,
    prefix_gdl_statements_to_prolog,
    prolog_term_to_prefix_gdl,
)

__all__ = [
    'GeneralGameManager',
    'GeneralGame',
    'GeneralGameState',
    'Role',
    'Action',
    'GameProposition',
]

logger = logging.getLogger(__name__)

# Read in game state rules
Functor('consult', 1)(Term.from_atom_name(
    os.path.join(prolog_dir, 'ggp_state.pl')))()


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
    _and_predicate = Predicate.from_name_arity(',', 2)

    def __init__(self):
        super().__init__()

        self._logger = logging.getLogger(__name__ + self.__class__.__name__)

    def __str__(self):
        return 'GeneralGameManager'

    def game_exists(self, game_id):
        """Return true if a game with id game_id has been created.

        Args:
            game_id (str) : Game ID string
        """
        with Frame():
            args = TermList(1)
            args[0].put_atom_name(game_id)
            return self._game_id_predicate(arglist=args)

    def create_game(self, game_id, game_description):
        """Create a game with the given game_id using the game description.

        Args:
            game_id (str)          : Game is created with this ID.
            game_description (str) : Game description given in Game Description
                Language (GDL).
        """
        with Frame():
            self._create_game_predicate(
                Term.from_atom_name(game_id),
                prefix_gdl_statements_to_prolog(game_description),
                check=True)

    def game(self, game_id):
        """Get a game by name.

        Args:
            game_id (str) : ID of game to retrieve.

        Returns:
            GeneralGame: Game with the given ID.
        """
        return GeneralGame(self, game_id)

    @staticmethod
    def _game_state_term_single(game_id_term, game_state, query):
        """Construct a term representing a fact about a game state.

        Args:
            game_id_term (swilite.Term) : The game ID.
            game_state   (swilite.Term) : The current game state.
            query        (swilite.Term) : Fact about the current game state.

        Returns:
            swilite.Term:
        """
        return GeneralGameManager._game_state_functor(
            game_id_term, game_state, query)

    @staticmethod
    def _game_state_term(game_id_term, game_state, *queries):
        """Construct a term representing one or more facts about a game state.

        Args:
            game_id_term (swilite.Term) : The game ID.
            game_state   (swilite.Term) : The current game state.
            *queries     (swilite.Term) : Facts about the current game state.

        Returns:
            swilite.Term:
        """
        queries = list(queries)
        term = GeneralGameManager._game_state_term_single(
            game_id_term, game_state, queries.pop())
        while queries:
            term = (GeneralGameManager._game_state_term_single(
                game_id_term, game_state, queries.pop()) & term)
        return term


class GeneralGame(object):
    """A general game."""
    _empty_game_state = Atom('none')
    _role_functor = Functor(Atom('role'), 1)
    _input_functor = Functor(Atom('input'), 2)
    _base_functor = Functor(Atom('base'), 1)

    def __init__(self, game_manager, game_id):
        self.game_manager = game_manager
        self.game_id = game_id

    def __str__(self):
        return self.game_id

    def __repr__(self):
        return 'GeneralGame(game_manager={!r}, game_id={!r})'.format(
            self.game_manager, self.game_id)

    def __eq__(self, other):
        return (self.game_manager == other.game_manager and
                self.game_id == other.game_id)

    def initial_state(self):
        """Return the initial state of the game as a GeneralGameState"""
        return GeneralGameState(self)

    def roles(self):
        """An iterator of the game roles.

        Yields:
            Role: A game role.
        """
        with Frame():
            role_variable = Term()
            role_query_term = self._role_functor(role_variable)

            with self._stateless_query(role_query_term) as q:
                while q.next_solution():
                    yield Role._from_atom(role_variable.get_atom())

    def num_roles(self):
        """The number of roles in the game."""
        return len(set(self.roles()))

    def all_actions(self, role):
        """Iterator over all possible actions for `role` in this game.

        This does not represent the legal actions in some state.
        It is an iterator of all actions which may be available to role at some
        time in the game.

        Args:
            role (Role) : Get actions for this role.

        Yields:
            Action: A possible action for `role` in this game.
        """
        with Frame() as f:
            action_variable = f.term()
            input_query_term = self._input_functor(
                Term.from_atom(role._atom), action_variable)

            query = self._stateless_query(input_query_term)
            for action in query.term_assignments(action_variable,
                                                 persistent=True):
                yield Action._from_term_record(action)

    def base_propositions(self):
        """An iterator over all base propositions of the game.

        A game state is defined by the subset of base propositions that are
        true for that state.
        """
        with Frame() as f:
            base_variable = f.term()
            base_query_term = self._base_functor(base_variable)

            query = self._stateless_query(base_query_term)
            for base_proposition in query.term_assignments(base_variable,
                                                           persistent=True):
                yield GameProposition._from_term_record(base_proposition)

    def max_utility(self):
        """Maximum utility achievable by any player."""
        return 100

    def min_utility(self):
        """Minimum utility achievable by any player."""
        return 0

    def _stateless_query_term(self, *queries):
        return self._stateful_query_term(
            Term.from_atom(self._empty_game_state), *queries)

    def _stateful_query_term(self, state, *queries):
        return self.game_manager._game_state_term(
            Term.from_atom_name(self.game_id), state, *queries)

    def _stateless_query(self, *queries):
        return self._stateful_query(
            Term.from_atom(self._empty_game_state), *queries)

    def _stateful_query(self, state, *queries):
        return Query.call_term(self.game_manager._game_state_term(
            Term.from_atom_name(self.game_id), state, *queries))


class Role():
    """A game role."""
    def __init__(self, role):
        """Initialize `Role` object from name.

        Args:
            role (str) : Name of the role.
        """
        self._atom = Atom(role)

    @classmethod
    def _from_atom(cls, atom):
        """Create `Role` object from a role atom.

        Args:
            role_atom (swilite.Atom) : Role to create.
        """
        new_role = cls.__new__(cls)
        new_role._atom = atom
        return new_role

    def __str__(self):
        """The role name as a string."""
        return str(self._atom)

    def __eq__(self, other):
        return self._atom == other._atom

    def __hash__(self):
        return hash(self._atom)


class _GdlTermRecordWrapper():
    def __init__(self, gdl):
        """Initialize by parsing a GDL string.

        Args:
            gdl (str) : GDL string to parse.
        """
        with Frame():
            self._term_record = TermRecord(
                prefix_gdl_statement_to_prolog(gdl))

    @classmethod
    def _from_term_record(cls, term_record):
        """Initialize from a term record."""
        obj = cls.__new__(cls)
        obj._term_record = term_record
        return obj

    def __str__(self):
        """Representation as a GDL string."""
        with Frame():
            return prolog_term_to_prefix_gdl(self._term_record.get())

    def __eq__(self, other):
        with Frame():
            try:
                return self._term_record.get() == other._term_record.get()
            except AttributeError as e:
                if '_term_record' not in str(e):
                    raise
                return NotImplemented


class Action(_GdlTermRecordWrapper):
    """A game action."""
    pass


class GameProposition(_GdlTermRecordWrapper):
    """A proposition about the game state."""
    pass


class GeneralGameState(object):
    """A general game state."""

    _terminal_atom = Atom('terminal')

    _base_functor = GeneralGame._base_functor
    _does_functor = Functor('does', 2)
    _eq_functor = Functor('=', 2)
    _goal_functor = Functor('goal', 2)
    _legal_functor = Functor('legal', 2)
    _true_functor = Functor('true', 1)
    _truth_history_3_functor = Functor('truth_history', 3)

    _final_truth_state_predicate = Predicate(
        functor=Functor('final_truth_state', 2),
        module=GeneralGameManager._ggp_state)
    _length_predicate = Predicate(functor=Functor('length', 2))
    _prepare_moves_predicate = Predicate(functor=Functor('prepare_moves', 3),
                                         module=GeneralGameManager._ggp_state)
    _truth_history_3_predicate = Predicate(
        functor=_truth_history_3_functor,
        module=GeneralGameManager._ggp_state)
    _truth_history_4_predicate = Predicate(
        functor=Functor('truth_history', 4),
        module=GeneralGameManager._ggp_state)

    def __init__(self, game,
                 move_history_term=None,
                 truth_history_term=None,
                 truth_state_term=None):
        self.game = game

        with Frame():
            if move_history_term is None:
                move_history_term = Term.from_nil()
            self.move_history = TermRecord(move_history_term)

            if truth_history_term is None:
                truth_history_term = Term()
                self._truth_history_3_predicate(
                    self._game_id_term(), move_history_term,
                    truth_history_term, check=True)
            self.truth_history = TermRecord(truth_history_term)

            if truth_state_term is None:
                truth_state_term = Term()
                self._final_truth_state_predicate(
                    truth_history_term, truth_state_term, check=True)
            self.truth_state = TermRecord(truth_state_term)

    def __eq__(self, other):
        return (self.game == other.game and
                (self.truth_state == other.truth_state or
                 self.truth_state.get() == other.truth_state.get()))

    def turn_number(self):
        """The current turn number."""
        with Frame():
            num_moves = Term()
            self._length_predicate(self.move_history.get(), num_moves,
                                   check=True)
            return int(num_moves)

    def utility(self, role):
        """The utility of the current state for the given role."""
        with Frame():
            utility = Term()
            utility_query = self._goal_functor(
                Term.from_atom(role._atom), utility)
            self._query_term(utility_query)(check=True)

            if utility.is_atom():
                return int(utility.get_atom_name())
            else:
                return int(utility)

    def legal_actions(self, role):
        """An iterator of legal actions for role in the current state."""
        with Frame() as f:
            action = f.term()
            action_query = self._legal_functor(
                Term.from_atom(role._atom), action)

            query = self._query(action_query)
            for action_assignment in query.term_assignments(action,
                                                            persistent=True):
                yield Action._from_term_record(action_assignment)

    def state_propositions(self):
        """Iterator of the base propositions that are true for this state."""
        with Frame() as f:
            state_term = f.term()
            base_term_query = self._base_functor(state_term)
            true_term_query = self._true_functor(state_term)

            query = self._query(base_term_query, true_term_query)
            for state_term_assignment in query.term_assignments(
                    state_term, persistent=True):
                yield GameProposition._from_term_record(
                    state_term_assignment)

    def is_terminal(self):
        """True if the current game state is terminal."""
        with Frame():
            return self._query_term(Term.from_atom(self._terminal_atom))()

    def apply_moves(self, moves):
        """A new game state representing the game after a move is applied.

        Returns a new state, this state is unchanged.

        Args:
            moves (dict) : Dict of `Role` => `Action`, one entry per role.

        Returns:
            GeneralGameState: The new game state.
        """
        with Frame() as f:
            game_id_term = self._game_id_term()

            moves_term = Term.from_list_terms([
                self._does_functor(Term.from_atom(role._atom),
                                   action._term_record.get())
                for (role, action) in moves.items()])

            # prepare_moves(game_id, moves_term, PreparedMoves)
            prepared_moves = f.term()
            try:
                self._prepare_moves_predicate(
                    game_id_term, moves_term, prepared_moves, check=True)
            except PrologCallFailed:
                raise ValueError(
                    'Invalid move set. Possibly not 1 move per role.')

            # NewMoveHistory = [PreparedMoves | old_move_history]
            new_move_history = Term.from_cons_list(prepared_moves,
                                                   self.move_history.get())

            # truth_history(game_id, NewMoveHistory, old_truth_history,
            #               NewTruthHistory)
            new_truth_history = f.term()
            try:
                self._truth_history_4_predicate(
                    game_id_term, new_move_history, self.truth_history.get(),
                    new_truth_history, check=True)
            except PrologCallFailed:
                raise ValueError('Invalid moves: {}'.format(
                    {str(role): str(action)
                     for role, action in moves.items()}))

            # final_truth_state(NewTruthHistory, NewTruthState)
            new_truth_state = f.term()
            self._final_truth_state_predicate(
                new_truth_history, new_truth_state, check=True)

            return GeneralGameState(
                game=self.game,
                move_history_term=new_move_history,
                truth_history_term=new_truth_history,
                truth_state_term=new_truth_state,
            )

    def game_id(self):
        return self.game.game_id

    def _game_id_term(self):
        return Term.from_atom_name(self.game_id())

    def _query_term(self, *queries):
        return self.game._stateful_query_term(self.truth_state.get(), *queries)

    def _query(self, *queries):
        return self.game._stateful_query(self.truth_state.get(), *queries)

import logging
import os.path

from pygdl.prolog import PrologSession
from pygdl.languages.prolog import (
    PrologAtom,
    PrologCompoundTerm,
    PrologList,
    PrologTerm,
)
from pygdl.paths import prolog_dir

logger = logging.getLogger(__name__)


class GeneralGameManager(object):
    """Manage game descriptions using SWI-Prolog"""

    _ggp_state_prolog_file = os.path.join(prolog_dir, 'ggp_state.pl')

    def __init__(self):
        super().__init__()

        self._logger = logging.getLogger(__name__ + self.__class__.__name__)
        self.prolog = PrologSession()

        self.prolog.consult(self._ggp_state_prolog_file)

    def game_exists(self, game_id):
        """Return true if a game with id game_id has been created."""
        return self.prolog.query_satisfied(
            'game_id({game_id!s})'.format(game_id=game_id))

    def create_game(self, game_id, rules):
        self.prolog.require_query(
            'create_game({game_id!s}, {rules!s})'.format(
                game_id=game_id, rules=PrologList(rules)))

    def game(self, game_id):
        """Get a GeneralGame object representing game_id"""
        return GeneralGame(self, game_id)

    @staticmethod
    def game_state_query_term_single(game_id, game_state, query):
        return PrologCompoundTerm(name='game_state',
                                  args=(game_id, game_state, query))

    @staticmethod
    def game_state_query_term(game_id, game_state, *queries):
        """Prolog term representing a query to a game state."""
        assert(queries)
        return PrologTerm.and_(*(
            PrologCompoundTerm(name='game_state',
                               args=(game_id, game_state, query))
            for query in queries))


class GeneralGameManagerKifInterface(object):
    """Interact with a GeneralGameManager using KIF instead of Prolog."""


class GeneralGame(object):
    """A general game."""
    def __init__(self, game_manager, game_id):
        self.game_manager = game_manager
        self.game_id = PrologAtom(name=game_id)

    def initial_state(self):
        """Return the initial state of the game as a GeneralGameState"""
        return GeneralGameState(self)

    def roles(self):
        """An iterator of the game roles (each a PrologTerm)"""
        return (assignment['Role']
                for assignment
                in self._prolog().query(
                    self.stateless_query_term('role(Role)')))

    def num_roles(self):
        """The number of roles in the game."""
        return len(set(self.roles()))

    def all_moves(self, role):
        """All possible moves for role in this game.

        This does not represent the legal moves in some state.
        It is an iterator of all mich which may be available to role at some
        time in the game.
        """
        return (assignment['Move']
                for assignment
                in self._prolog().query(
                    self.stateless_query_term(
                        PrologCompoundTerm(name='input', args=(role, 'Move')))))

    def base_terms(self):
        """A list of the terms which define the game state."""
        return (assignment['X']
                for assignment in self._prolog().query(
                    self.stateless_query_term('base(X)')))

    def stateless_query_term(self, *queries):
        return self.stateful_query_term(PrologAtom('none'), *queries)

    def stateful_query_term(self, state, *queries):
        return self.game_manager.game_state_query_term(
            self.game_id, state, *queries)

    def _prolog(self):
        return self.game_manager.prolog


class GeneralGameState(object):
    """A general game state."""
    def __init__(self, game,
                 move_history=None,
                 truth_history=None,
                 truth_state=None):
        self.game = game

        if move_history is None:
            self.move_history = PrologList()
        else:
            self.move_history = move_history

        if truth_history is None:
            assert truth_state is None
            assignment = self._prolog().query_first(
                PrologTerm.and_(
                    PrologCompoundTerm(
                        name='truth_history',
                        args=(self.game_id(), self.move_history,
                              'TruthHistory')),
                    'final_truth_state(TruthHistory, TruthState)'))

            self.truth_history = assignment['TruthHistory']
            self.truth_state = assignment['TruthState']
        else:
            self.truth_history = truth_history

            if truth_state is None:
                assignment = self._prolog().query_first(
                    PrologCompoundTerm(
                        name='final_truth_state',
                        args=(self.truth_history, 'TruthState')))
                self.truth_state = assignment['TruthState']
            else:
                self.truth_state = truth_state

    def turn_number(self):
        """The current turn number."""
        return len(self.move_history)

    def utility(self, role):
        """The utility of the current state for the given role."""
        return int(self._prolog().query_first(
            self.query_term(PrologCompoundTerm(
                name='goal',
                args=(role, 'Utility'))))['Utility'])

    def legal_moves(self, role):
        """An iterator of legal moves for role in the current state."""
        return (assignment['Move']
                for assignment
                in self._prolog().query(
                    self.query_term(
                        PrologCompoundTerm(name='legal', args=(role, 'Move')))))

    def state_terms(self):
        """Iterator of the base terms that are true for this state."""
        return (assignment['X']
                for assignment
                in self._prolog().query(
                    self.query_term('base(X)', 'true(X)')))

    def is_terminal(self):
        """True if the current game state is terminal."""
        return self._prolog().query_satisfied(self.query_term('terminal'))

    def apply_move(self, moves):
        """A new game state representing the game after moves are applied.

        Returns a new state, this state is unchanged.
        moves is a dictionary of role => move.
        """
        moves_term = PrologList(tuple(
            PrologCompoundTerm(name='does', args=(role, action))
            for (role, action) in moves.items()))
        print("Moves Term:", str(moves_term))
        print("Old Move History:", str(self.move_history))

        assignment = self._prolog().query_first(
            PrologTerm.and_(
                PrologCompoundTerm(
                    name='prepare_moves',
                    args=(self.game_id(), moves_term, 'PreparedMoves')),
                PrologCompoundTerm(
                    name='=',
                    args=('MoveHistory',
                          PrologCompoundTerm(
                              name='[|]',
                              args=('PreparedMoves', self.move_history)))),
                PrologCompoundTerm(
                    name='truth_history',
                    args=(self.game_id(), 'MoveHistory',
                          self.truth_history, 'TruthHistory')),
                'final_truth_state(TruthHistory, TruthState)',
            ))
        return GeneralGameState(
            game=self.game,
            move_history=assignment['MoveHistory'],
            truth_history=assignment['TruthHistory'],
            truth_state=assignment['TruthState'],
        )

    def query_term(self, *queries):
        return self.game.stateful_query_term(self.truth_state, *queries)

    def game_id(self):
        return self.game.game_id

    def _prolog(self):
        return self.game.game_manager.prolog

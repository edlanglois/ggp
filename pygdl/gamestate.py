import copy
import logging
import os.path

from pygdl.pyswipl.extras import consult, make_and_term, and_functor
from pygdl.pyswipl.prolog import (
    Atom,
    Functor,
    Module,
    Predicate,
    Query,
    Term,
    TermList,
)
from pygdl.languages.prolog import (
    PrologCompoundTerm,
    PrologList,
)
from pygdl.paths import prolog_dir

logger = logging.getLogger(__name__)


class GeneralGameManager(object):
    """Manage game descriptions using SWI-Prolog"""

    _ggp_state_prolog_file = os.path.join(prolog_dir, 'ggp_state.pl')
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
        consult(self._ggp_state_prolog_file)

    def game_exists(self, game_id):
        """Return true if a game with id game_id has been created."""
        args = TermList(1)
        args.head.put_atom_name(game_id)
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

    @staticmethod
    def game_state_term_single(game_id, game_state, query):
        """Construct a term representing a fact about a game state.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            query      (prolog.Term) : Fact about the current game state.

        Returns:
            prolog.Term:
        """
        return Term.from_cons_functor(GeneralGameManager.game_state_functor,
                                      game_id, game_state, query)

    @staticmethod
    def game_state_term(game_id, game_state, *queries):
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
            GeneralGameManager.game_state_term_single(
                game_id, game_state, queries[0])
        else:
            return make_and_term(*(
                GeneralGameManager.game_state_term_single(
                    game_id, game_state, query)
                for query in queries))

    @staticmethod
    def game_state_query_single(game_id, game_state, query):
        """Construct a query of a game state fact.

        Args:
            game_id    (prolog.Term) : The game ID.
            game_state (prolog.Term) : The current game state.
            query      (prolog.Term) : Fact about the current game state.

        Returns:
            prolog.Query:
        """
        args = TermList(3)
        args[0].put_term(game_state)
        args[1].put_term(game_id)
        args[2].put_term(query)
        return Query(predicate=GeneralGameManager._game_id_predicate,
                     arguments=args)

    @staticmethod
    def game_state_query(game_id, game_state, *queries):
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
            return GeneralGameManager.game_state_query_single(
                game_id, game_state, queries[0])
        else:
            args = TermList(2)
            args[0].put_term(GeneralGameManager.game_state_term_single(
                game_id, game_state, queries[0]))
            args[1].put_term(GeneralGameManager.game_state_term(
                game_id, game_state, queries[1:]))
            return Query(predicate=GeneralGameManager._and_predicate,
                         args=args)


class GeneralGame(object):
    """A general game."""

    _empty_game_state_term = Term.from_atom_name('none')
    _role_functor = Functor(Atom('role'), 1)
    _input_functor = Functor(Atom('input'), 2)
    _base_functor = Functor(Atom('base'), 1)

    def __init__(self, game_manager, game_id):
        self.game_manager = game_manager
        self.game_id = Term.from_atom_name(game_id)

    def initial_state(self):
        """Return the initial state of the game as a GeneralGameState"""
        roles = self.roles()
        rl = list(roles)
        print(rl)
        import pdb; pdb.set_trace()  # XXX BREAKPOINT
        return GeneralGameState(self)

    def roles(self):
        """An iterator of the game roles (each a PrologTerm)"""
        role_query_term = Term.from_functor(self._role_functor)
        role_variable = role_query_term[0]

        with self.stateless_query(role_query_term) as q:
            while q.next_solution():
                yield role_variable.get_atom()

    def num_roles(self):
        """The number of roles in the game."""
        return len(set(self.roles()))

    def all_moves(self, role):
        """All possible moves for role in this game.

        This does not represent the legal moves in some state.
        It is an iterator of all moves which may be available to role at some
        time in the game.
        """
        if not isinstance(role, Atom):
            role = Atom(role)

        input_query_term = Term.from_functor(self._input_functor)
        input_query_term[0].put_atom(role)
        move_variable = input_query_term[1]

        with self.stateless_query(input_query_term) as q:
            while q.next_solution():
                yield copy.deepcopy(move_variable)

    def base_terms(self):
        """A list of the terms which define the game state."""
        base_query_term = Term.from_functor(self._base_functor)
        base_variable = base_query_term[0]

        with self.stateless_query(base_query_term) as q:
            while q.next_solution():
                yield copy.deepcopy(base_variable)

    def max_utility(self):
        """Maximum utility achievable by any player."""
        return 100

    def min_utility(self):
        """Minimum utility achievable by any player."""
        return 0

    def stateless_query_term(self, *queries):
        return self.stateful_query_term(self._empty_game_state_term, *queries)

    def stateful_query_term(self, state, *queries):
        return self.game_manager.game_state_term(self.game_id, state, *queries)

    def stateless_query(self, *queries):
        return self.stateful_query(self._empty_game_state_term, *queries)

    def stateful_query(self, state, *queries):
        return self.game_manager.game_state_query(self.game_id, state, *queries)


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
            assignment = self._prolog().query_first((
                'truth_history({game_id!s}, {move_history!s}, TruthHistory), '
                'final_truth_state(TruthHistory, TruthState)').format(
                    game_id=self.game_id(),
                    move_history=self.move_history))

            self.truth_history = assignment['TruthHistory']
            self.truth_state = assignment['TruthState']
        else:
            self.truth_history = truth_history

            if truth_state is None:
                assignment = self._prolog().query_first(
                    'final_truth_state({truth_history!s}, TruthState)'.format(
                        truth_history=self.truth_history))
                self.truth_state = assignment['TruthState']
            else:
                self.truth_state = truth_state

    def turn_number(self):
        """The current turn number."""
        return len(self.move_history)

    def utility(self, role):
        """The utility of the current state for the given role."""
        return int(self._prolog().query_first(
            self.query_term('goal({role!s}, Utility)'.format(
                role=role)))['Utility'].name)

    def legal_moves(self, role):
        """An iterator of legal moves for role in the current state."""
        return (assignment['Move']
                for assignment
                in self._prolog().query(
                    self.query_term('legal({role!s}, Move)'.format(role=role))
                ))

    def state_terms(self):
        """Iterator of the base terms that are true for this state."""
        return (assignment['X']
                for assignment
                in self._prolog().query(
                    self.query_term('base(X)', 'true(X)')))

    def is_terminal(self):
        """True if the current game state is terminal."""
        return self._prolog().query_satisfied(self.query_term('terminal'))

    def apply_moves(self, moves):
        """A new game state representing the game after moves are applied.

        Returns a new state, this state is unchanged.
        `moves` is a dictionary of role => move.
        """
        moves_term = PrologList(tuple(
            PrologCompoundTerm(name='does', args=(role, action))
            for (role, action) in moves.items()))

        # moves_term = PL_new_term_ref()
        # putList(moves_term,
        #         [self.pyswip_does_functor(pyswip.Atom(role),
        #                                   ryswip.

        assignment = self._prolog().query_first((
            'prepare_moves({game_id!s}, {moves_term!s}, PreparedMoves),'
            'MoveHistory = [PreparedMoves | {old_move_history!s}],'
            'truth_history({game_id!s}, MoveHistory, {old_truth_history!s},'
            '              TruthHistory),'
            'final_truth_state(TruthHistory, TruthState)').format(
                game_id=self.game_id(),
                moves_term=moves_term,
                old_move_history=self.move_history,
                old_truth_history=self.truth_history))

        print('-----------------')
        print(assignment)
        print('\n\n')
        print(assignment.keys())
        print('\n\n')
        print({key: len(str(value)) for key, value in assignment.items()})
        print('\n\n')

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

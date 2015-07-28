import logging
import random

from pyswip import Prolog, Functor, Atom

from pygdl.kif import (kif_to_prolog,
                       kif_s_expr_to_prolog,
                       single_kif_term_to_prolog)
from pygdl.sexpr import (parse_s_expressions,
                         prefix_functional_to_s_expressions,
                         to_s_expression_string)

logger = logging.getLogger(__name__)


class QueryEvaluatesFalseError(Exception):
    def __init__(self, query):
        self.query = query

    def __str__(self):
        return "Query: " + self.query


class PrologTerm(object):
    """Representation of a Prolog term."""
    def __init__(self, obj):
        super().__init__()
        self.obj = obj

    def __repr__(self):
        return "{}({!r})".format(PrologTerm.__name__, self.obj)

    def __str__(self):
        """Return the term as a Prolog string."""
        if isinstance(self.obj, Functor):
            # Default str(Functor()) does not give a Prolog string
            return "{!s}({!s})".format(
                self.obj.name,
                ", ".join(str(PrologTerm(arg))
                          for arg in self.obj.args))
        else:
            return str(self.obj)


class PrologGameState(object):
    """Manage a game state with Prolog."""
    def __init__(self):
        super().__init__()
        self.prolog = Prolog()
        self.is_game_specified = False

        # Prolog() is a singleton class so make sure that this is the only
        # GameState using it.
        id_ = random.randint(0, 10**10)
        self.prolog.assertz('pygdl_game_state_id({!s})'.format(id_))
        assert sum(1 for _ in self.query('pygdl_game_state_id(X)')) == 1, \
            "Cannot create more than one instance of GameState"

        # Rules used for evaluating game states
        self.prolog.assertz('distinct(X, Y) :- dif(X, Y)')
        self.prolog.dynamic('turn/1')
        self.prolog.dynamic('does/2')
        self.prolog.dynamic('true/1')
        self.prolog.dynamic('nexttrue/1')
        self.prolog.assertz(
            """update :-
                forall(role(Role),
                       (findall(Move, does(Role, Move), MoveList),
                        length(MoveList, L),
                        L == 1,
                        does(Role, Move),
                        legal(Role, Move))),
                forall(base(Fact), (not(next(Fact)); assert(nexttrue(Fact)))),
                retractall(true(_)),
                forall(nexttrue(Fact), assert(true(Fact))),
                retractall(nexttrue(_)),
                turn(T),
                succ(T, U),
                assert(turn(U)),
                retract(turn(T))
            """)
        self.prolog.assertz(
            """setmove(Role, Move) :-
                role(Role),
                legal(Role, Move),
                retractall(does(Role, _)),
                assert(does(Role, Move))
            """)

    def load_game_from_facts(self, facts):
        """Load game from a list of prolog fact strings."""
        for fact in facts:
            self.prolog.assertz(fact)

        self.is_game_specified = True
        self.start_game()

    def start_game(self):
        """(Re)start the game with no moves played."""
        assert(self.is_game_specified)
        self.prolog.retractall('turn(_)')
        self.prolog.assertz('turn(1)')
        self.prolog.retractall('true(_)')
        self.require_query('forall(init(Fact), assert(true(Fact)))')

    def get_roles(self):
        """An iterable of PrologTerm, each containing a role."""
        return (assignment['Role']
                for assignment in self.query('role(Role)'))

    def get_legal_moves(self, role):
        """An iterable of PrologTerm, each containing a legal move for role."""
        role = str(role)
        assert(role == role.lower())
        return (assignment['Move']
                for assignment in self.query('legal({!s}, Move)'.format(role)))

    def get_turn(self):
        """Return the current turn number."""
        return self.query_single('turn(Turn)')['Turn'].obj

    def get_utility(self, role):
        """Return the utility of the current state for the given role."""
        return self.query_single('goal({!s}, U)'.format(role))['U'].obj

    def get_base_terms(self):
        """Return a list of terms which define the game state."""
        return (assignment['X'] for assignment in self.query('base(X)'))

    def get_state_terms(self):
        """Return the base terms that are true for the current state."""
        return (assignment['X']
                for assignment in self.query('base(X), true(X)'))

    def set_move(self, role, move):
        """Set `role` to make `move` at the current turn."""
        role = str(role)
        move = str(move)
        logger.debug("setmove(%s, %s)", role, move)
        assert(role == role.lower())
        assert(move == move.lower())
        self.require_query('setmove({!s}, {!s})'.format(role, move))

    def next_turn(self):
        """Advance to the next turn.

        All roles make the moves specified by `set_move`
        """
        self.require_query('update')

    def is_terminal(self):
        """Return True if the current game state is terminal."""
        return self.boolean_query('terminal')

    def query_single(self, query_string):
        """Evaluate query_string and return the single resulting assignment.

        Raises an exception if the query results in anything other than one
        term.
        """
        query_results = self.query(query_string)
        try:
            result = next(query_results)
            try:
                next(query_results)
            except StopIteration:
                return result

            raise AssertionError("Query yielded > 1 assignment.")
        except StopIteration:
            raise AssertionError("Query yielded no assignments.")

    def require_query(self, query_string):
        """Execute query_string and raise exception if it evaluates false.

        Raises QueryEvaluatesFalseError
        """
        if not self.boolean_query(query_string):
            raise QueryEvaluatesFalseError(query_string)

    def boolean_query(self, query_string):
        """Return True if query_string has at least 1 satisfying assignment."""
        query_results = self.query(query_string)
        try:
            next(query_results)
            query_results.close()
            return True
        except StopIteration:
            return False

    def query(self, query_string):
        """Execute query_string and return results.

        Returns an iterable of assignments, where each assignment is
        a dictionary that maps Variable => PrologTerm.

        If the query has no variables and is satisfied, a single '[]'
        PrologTerm is yielded.

        WARNING: The returned iterator must be consumed before executing the
        next query.
        """
        for assignment in self.prolog.query(query_string, normalize=False):
            if isinstance(assignment, Atom):
                yield PrologTerm(assignment)
            else:
                yield {str(PrologTerm(equality.args[0])):
                       PrologTerm(equality.args[1])
                       for equality in assignment}


class KIFTerm(object):
    """Representation of a KIF term."""

    def __init__(self, kif_term, is_s_expression=False):
        if is_s_expression:
            self.s_expression = kif_term
        else:
            s_expressions = list(parse_s_expressions([str(kif_term)]))
            assert len(s_expressions) == 1
            self.s_expression = s_expressions[0]

    @staticmethod
    def from_prolog(prolog_term):
        """Generate a KIF term from a prolog string."""
        s_expressions = \
            list(prefix_functional_to_s_expressions([str(prolog_term)]))
        assert len(s_expressions) == 1
        return KIFTerm(s_expressions[0], is_s_expression=True)

    def __str__(self):
        return to_s_expression_string(self.s_expression)


class KIFGameState(object):
    """Wrapper around PrologGameState providing a KIF interface."""
    def __init__(self):
        super().__init__()
        self.prolog_game_state = PrologGameState()

    def load_game_from_file(self, filename):
        """Load the game description from a KIF file"""
        with open(filename, 'r') as f:
            self.load_game_from_lines(f)

    def load_game_from_lines(self, lines):
        """Load the game description from KIF lines."""
        self.prolog_game_state.load_game_from_facts(kif_to_prolog(lines))

    def load_game_from_s_expressions(self, s_expressions):
        """Load the game description from KIF S-expressions"""
        self.prolog_game_state.load_game_from_facts(
            kif_s_expr_to_prolog(s_expr) for s_expr in s_expressions)

    def start_game(self):
        """(Re)start the game with no moves played."""
        self.prolog_game_state.start_game()

    def get_roles(self):
        """An iterable of KIFTerm, each containing a role."""
        return self.prolog_assignments_to_kif(
            self.prolog_game_state.get_roles())

    def get_legal_moves(self, role):
        """An iterable of KIFTerm, each containing a legal move for role."""
        return self.prolog_assignments_to_kif(
            self.prolog_game_state.get_legal_moves(
                single_kif_term_to_prolog(str(role))))

    def get_turn(self):
        """Return the current turn number"""
        return self.prolog_game_state.get_turn()

    def get_utility(self, role):
        """Return the utility of the current state for the given role."""
        return self.prolog_game_state.get_utility(role)

    def get_base_terms(self):
        """Return a list of terms which define the game state."""
        return self.prolog_assignments_to_kif(
            self.prolog_game_state.get_base_terms())

    def get_state_terms(self):
        """Return the base terms that are true for the current state."""
        return self.prolog_assignments_to_kif(
            self.prolog_game_state.get_state_terms())

    def set_move(self, role, move):
        """Set `role` to make `move` at the current turn."""
        return self.prolog_game_state.set_move(
            single_kif_term_to_prolog(str(role)),
            single_kif_term_to_prolog(str(move)))

    def next_turn(self):
        """Advance to the next turn.

        All roles make the moves specified by `set_move`
        """
        return self.prolog_game_state.next_turn()

    def is_terminal(self):
        """Return True if the current game state is terminal."""
        return self.prolog_game_state.is_terminal()

    @staticmethod
    def prolog_assignments_to_kif(assignments):
        for assignment in assignments:
            yield KIFGameState.prolog_assignment_to_kif(assignment)

    @staticmethod
    def prolog_assignment_to_kif(assignment):
        if isinstance(assignment, PrologTerm):
            return KIFTerm.from_prolog(assignment)
        else:
            return {variable: KIFTerm.from_prolog(equality)
                    for variable, equality in assignment.iteritems()}

from pyswip import Prolog, Functor, Atom

from pygdl.kif import kif_to_prolog

class GameObject(object):
    def __init__(self, obj):
        self.obj = obj

    def __repr__(self):
        return "GameObject({!r})".format(self.obj)

    def __str__(self):
        if isinstance(self.obj, Atom):
            return str(self.obj)
        elif isinstance(self.obj, Functor):
            return "{!s}({!s})".format(
                self.obj.name,
                ", ".join(str(GameObject(arg))
                          for arg in self.obj.args))
        else:
            return str(self.obj)


class QueryEvaluatesFalseError(Exception):
    def __init__(self, query):
        self.query = query

    def __str__(self):
        return "Query: " + query


class GameState(object):
    def __init__(self):
        super().__init__()
        self.prolog = Prolog()

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
                forall(next(Fact), assert(nexttrue(Fact))),
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

    def load_game_from_file(self, kif_file):
        """Load the game description from a KIF file."""
        with open(kif_file, 'r') as f:
            for fact in kif_to_prolog(f):
                self.prolog.assertz(fact)

        self.start_game()

    def start_game(self):
        """(Re)start the game with no moves played."""
        self.prolog.retractall('turn(_)')
        self.prolog.assertz('turn(1)')
        self.prolog.retractall('true(_)')
        self.require_query('forall(init(Fact), assert(true(Fact)))')

    def get_roles(self):
        return (assignment['Role']
                for assignment in self.query('role(Role)'))

    def get_legal_moves(self, role):
        assert(role == role.lower())
        return (assignment['Move']
                for assignment in self.query('legal({!s}, Move)'.format(role)))

    def get_turn(self):
        turns = list(assignment['Turn']
                     for assignment in self.query('turn(Turn)'))
        assert(len(turns) == 1)
        return turns[0]

    def set_move(self, role, move):
        assert(role == role.lower())
        assert(move == move.lower())
        return self.require_query('setmove({!s}, {!s})'.format(role, move))

    def next_turn(self):
        return self.requery_query('update')

    def is_terminal(self):
        return self.boolean_query('terminal')

    def require_query(self, query_string):
        """Execute query_string and raise exception if it evaluates false.

        Raises QueryEvaluatesFalseError
        """
        if not self.boolean_query(query_string):
            raise QueryEvaluatesFalseError(query_string)

    def boolean_query(self, query_string):
        return any(True for _ in self.query(query_string))

    def query(self, query_string):
        for assignment in self.prolog.query(query_string, normalize=False):
            if isinstance(assignment, Atom):
                yield GameObject(assignment)
            else:
                yield {str(GameObject(equality.args[0])):
                       GameObject(equality.args[1])
                       for equality in assignment}

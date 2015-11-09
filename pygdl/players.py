from collections import OrderedDict
import logging
import random
import itertools

__all__ = [
    'AlphaBeta',
    'CompulsiveDeliberation',
    'GamePlayer',
    'Legal',
    'Minimax',
    'ParameterDescription',
    'PlayerFactory',
    'Random',
    'SearchPlayer',
    'SequentialPlanner',
]

logger = logging.getLogger(__name__)


class PlayerFactory(object):
    """Player factory for GamePlayer"""
    def __init__(self, player_class, **player_init_kwargs):
        super().__init__()

        assert (set(player_init_kwargs.keys()) ==
                set(player_class.PARAMETER_DESCRIPTIONS.keys())),\
            'Given arguments {!s} but expecting {!s}'.format(
                set(player_init_kwargs.keys()),
                set(player_class.PARAMETER_DESCRIPTIONS.keys()))

        self.player_class = player_class
        self.player_init_kwargs = player_init_kwargs

    def __call__(self, game, role, start_clock, play_clock):
        return self.player_class(game=game,
                                 role=role,
                                 start_clock=start_clock,
                                 play_clock=play_clock,
                                 **self.player_init_kwargs)

    def player_name(self):
        return self.player_class.__name__


class ParameterDescription(object):
    PARAMS = ['type', 'help', 'choices']

    def __init__(self, **kwargs):
        super().__init__()

        expected_args = set(self.PARAMS)
        received_args = set(kwargs.keys())
        if received_args - expected_args:
            raise TypeError(
                '__init__ received unexpected argument(s) {}'.format(
                    received_args - expected_args))

        self.dict = kwargs


class GamePlayer(object):
    MIN_SCORE = 0
    MAX_SCORE = 100

    PARAMETER_DESCRIPTIONS = OrderedDict()

    def __init__(self, game, role, start_clock, play_clock):
        self.logger = logging.getLogger(__name__ + self.__class__.__name__)
        self.logger.info('Created {!s} with role "{!s}"'.format(
            self.__class__.__name__, role))
        self.game = game
        self.play_clock = play_clock

        self.role = self.game.role_object(role)
        self.roles = tuple(self.game.roles())
        self.game_state = self.game.initial_state()

    @classmethod
    def player_name(cls):
        return cls.__class__.__name__

    def update_moves(self, new_moves):
        assert(len(self.roles) == len(new_moves))

        self.logger.debug("GAME DESCRIPTION FOR TURN %s",
                          self.game_state.turn_number())
        for base in self.game_state.state_terms(persistent=False):
            self.logger.debug("\t%s", str(base))

        moves = {role: self.game.action_object(str(action))
                 for role, action in zip(self.roles, new_moves)}

        self.game_state = self.game_state.apply_moves(moves)

    def stop(self):
        self.logger.info('Stopping game. Terminal: {!s}. Score: {!s}'.format(
            self.game_state.is_terminal(),
            self.game_state.utility(self.role)))

    def abort(self):
        self.logger.info('Aborting game.')


class Legal(GamePlayer):
    """Plays the first legal move."""
    def get_move(self):
        actions = self.game_state.legal_actions(self.role, persistent=False)
        try:
            return str(next(actions))
        finally:
            actions.close()


class Random(GamePlayer):
    """Plays a random legal move."""
    def get_move(self):
        random_action = None
        for i, action in enumerate(
                self.game_state.legal_actions(self.role, persistent=False)):
            if random.randint(0, i) == 0:
                random_action = str(action)

        return random_action


class SearchPlayer(GamePlayer):
    def score_estimate_and_move_sequence(self, game_state, **kwargs):
        raise NotImplementedError

    def init_score_estimate_kwargs(self):
        return {}

    def get_best_move_sequence(self):
        _, move_sequence = self.get_best_score_and_move_sequence(
            score_matters=False)
        return move_sequence

    def get_best_score_and_move_sequence(self, score_matters=True):
        return self.score_estimate_and_move_sequence(
            game_state=self.game_state,
            score_matters=score_matters,
            **self.init_score_estimate_kwargs())

    def extract_own_move(self, move_sequence_element):
        try:
            return move_sequence_element[self.role]
        except TypeError:
            return move_sequence_element

    def get_move(self):
        score, move_sequence = self.get_best_score_and_move_sequence(
            score_matters=False)
        logger.debug('Score: {}'.format(score))
        logger.debug('Move sequence:')
        for move in move_sequence:
            try:
                logger.debug('\t{}'.format('\t'.join(
                    '{!s}: {!s}'.format(*item) for item in move.items())))
            except AttributeError:
                logger.debug('\t{!s}'.format(move))

        return self.extract_own_move(move_sequence[0])


class SimpleDepthFirstSearch(SearchPlayer):
    def __init__(self, game, role, start_clock, play_clock):
        super().__init__(game, role, start_clock, play_clock)
        assert self.game.num_roles() == 1, \
            "SimpleDepthFirstSearch only works for single-player games."

    def score_estimate_and_move_sequence(self, game_state):
        if game_state.is_terminal():
            return game_state.utility(self.role), tuple()

        moves = tuple(game_state.legal_actions(self.role, persistent=True))

        best_score = self.MIN_SCORE - 1
        best_move_sequence = tuple()

        for move_record in moves:
            move = move_record.get()
            score, move_sequence = self.score_estimate_and_move_sequence(
                game_state=game_state.apply_moves({self.role: move}))

            assert score >= self.MIN_SCORE
            assert score <= self.MAX_SCORE

            if score > best_score:
                best_score = score
                best_move_sequence = (str(move),) + move_sequence

            if best_score == self.MAX_SCORE:
                break

        return best_score, best_move_sequence


class CompulsiveDeliberation(SimpleDepthFirstSearch):
    """For each move, find optimal move with DFS."""
    pass


class SequentialPlanner(SimpleDepthFirstSearch):
    """On init, find optimal move sequence with DFS. Save and replay it."""
    def __init__(self, game, role, start_clock, play_clock):
        super().__init__(game, role, start_clock, play_clock)
        move_sequence = self.get_best_move_sequence()
        self.move_sequence = list(move_sequence)

    def get_move(self):
        return self.extract_own_move(self.move_sequence.pop(0))


class Minimax(SearchPlayer):
    def __init__(self, game, role, start_clock, play_clock):
        super().__init__(game, role, start_clock, play_clock)
        own_role_str = str(self.role)
        self.other_roles = tuple(
            other_role for other_role in self.game.roles()
            if str(other_role) != own_role_str)
        self.max_utility = self.game.max_utility()
        self.min_utility = self.game.min_utility()

    def init_score_estimate_kwargs(self):
        return {'prev_min_step_score': self.max_utility + 1,
                'depth': 0}

    def score_estimate_and_move_sequence(self,
                                         game_state,
                                         score_matters,
                                         depth,
                                         prev_min_step_score):

        non_rec_found, non_rec_estimate, non_rec_moves = \
            self.non_recursive_score_estimate_and_move_sequence(
                game_state, depth=depth)
        if non_rec_found:
            return non_rec_estimate, non_rec_moves

        own_moves = tuple(
            action.get() for action
            in tuple(game_state.legal_actions(self.role, persistent=True)))
        assert own_moves

        if not score_matters and len(own_moves) == 1:
            return None, (own_moves[0],)

        other_roles_move_lists = tuple(
            tuple((role, move_record.get()) for move_record
                  in tuple(game_state.legal_actions(role, persistent=True)))
            for role in self.other_roles)
        assert all(move_list for move_list in other_roles_move_lists)

        max_step_score = self.min_utility - 1
        max_step_score_move_sequence = ()

        for own_move in own_moves:
            min_step_score = self.max_utility + 1
            min_step_score_move_sequence = ()

            for other_roles_moves in itertools.product(*other_roles_move_lists):
                moves = dict(other_roles_moves + ((self.role, own_move),))
                score, move_sequence = self.score_estimate_and_move_sequence(
                    game_state=game_state.apply_moves(moves),
                    score_matters=True,
                    depth=(depth + 1),
                    prev_min_step_score=min_step_score)
                assert score >= self.min_utility
                assert score <= self.max_utility

                # Min
                if score < min_step_score:
                    min_step_score = score
                    min_step_score_move_sequence = (moves,) + move_sequence

                if self.min_step_break(score, max_step_score):
                    break

            # Max
            if min_step_score > max_step_score:
                max_step_score = min_step_score
                max_step_score_move_sequence = min_step_score_move_sequence

            if self.max_step_break(max_step_score, prev_min_step_score):
                break

        return max_step_score, max_step_score_move_sequence

    def min_step_break(self, score, max_step_score):
        return score == self.min_utility

    def max_step_break(self, score, min_step_score):
        return score == self.max_utility

    def non_recursive_score_estimate_and_move_sequence(self, game_state, depth):
        if game_state.is_terminal():
            return True, game_state.utility(self.role), ()
        return False, None, None


class AlphaBeta(Minimax):
    """Runs Minimax algorithm with Alpha-Beta pruning to decide each move."""
    def min_step_break(self, score, max_step_score):
        return (score == self.min_utility or  # Can't get any lower.
                score <= max_step_score)  # Will be rejected by prev. max step.

    def max_step_break(self, score, min_step_score):
        return (score == self.max_utility or  # Can't get any higher.
                score >= min_step_score)  # Will be rejected by prev. min step.


class BoundedDepth(AlphaBeta):
    """Runs bounded depth search on each move."""

    PARAMETER_DESCRIPTIONS = OrderedDict([
        ('max_depth', ParameterDescription(
            type=int, help='Maximum search depth.')),
        ('heuristic', ParameterDescription(
            type=str, choices=['zero', 'utility', 'mobility'],
            help='Heuristic method.')),
    ])

    def __init__(self, game, role, start_clock, play_clock, max_depth,
                 heuristic):
        super().__init__(game, role, start_clock, play_clock)
        self.max_depth = max_depth
        self.logger.debug('Max depth: {}'.format(max_depth))

        if heuristic == 'zero':
            self.heuristic_function = self.heuristic_zero
        elif heuristic == 'utility':
            self.heuristic_function = self.heuristic_utility
        elif heuristic == 'mobility':
            self.heuristic_function = self.heuristic_mobility
        else:
            raise ValueError('Unknown heuristic {}'.format(heuristic))

        self.num_possible_moves = {
            str(role_): len(set(
                str(action)
                for action in self.game.all_actions(role_, persistent=False)))
            for role_ in self.roles
        }

    def non_recursive_score_estimate_and_move_sequence(self, game_state, depth):
        if game_state.is_terminal():
            return True, game_state.utility(self.role), ()
        elif depth >= self.max_depth:
            return True, self.heuristic_function(game_state), ()
        else:
            return False, None, None

    def heuristic_zero(self, game_state):
        return 0

    def heuristic_utility(self, game_state):
        return game_state.utility(self.role)

    def heuristic_mobility(self, game_state):
        return (
            len(set(str(action) for action
                in game_state.legal_actions(self.role, persistent=False))) /
            self.num_possible_moves[str(self.role)])

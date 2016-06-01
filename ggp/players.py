from collections import OrderedDict
import itertools
import logging
import math
import operator
import random
import signal

import ggp.gamestate

__all__ = [
    'AlphaBeta',
    'CompulsiveDeliberation',
    'GamePlayer',
    'Legal',
    'Minimax',
    'MonteCarloTreeSearch',
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
    PARAMS = ['type', 'help', 'choices', 'default']

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

        self.role = ggp.gamestate.Role(role)
        self.roles = tuple(self.game.roles())
        self.game_state = self.game.initial_state()

    @classmethod
    def player_name(cls):
        return cls.__class__.__name__

    def _moves_dict(self, action_list):
        assert(len(self.roles) == len(action_list))
        return {role: ggp.gamestate.Action(action)
                for role, action in zip(self.roles, action_list)}

    def update_moves(self, new_moves):
        assert(len(self.roles) == len(new_moves))

        self.logger.debug("GAME DESCRIPTION FOR TURN %s",
                          self.game_state.turn_number())
        for role in self.roles:
            logger.debug('Utility for {role!s}: {utility!s}'.format(
                role=role, utility=self.game_state.utility(role)))
        for prop in self.game_state.state_propositions():
            self.logger.debug("\t%s", str(prop))

        moves = self._moves_dict(action_list=new_moves)
        self.game_state = self.game_state.apply_moves(moves)

    def stop(self):
        self.logger.info('Stopping game. Terminal: {!s}. Score: {!s}'.format(
            self.game_state.is_terminal(),
            self.game_state.utility(self.role)))

    def abort(self):
        self.logger.info('Aborting game.')


class AlarmContextManager(object):
    alarm_active = False

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        assert not AlarmContextManager.alarm_active, \
            'Only one alarm may be active at a time.'
        self.time_up = False
        self.old_alarm_handler = signal.signal(signal.SIGALRM,
                                               self.alarm_handler)
        AlarmContextManager.alarm_active = True
        signal.alarm(self.seconds)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        signal.alarm(0)
        AlarmContextManager.alarm_active = False
        signal.signal(signal.SIGALRM, self.old_alarm_handler)
        del self.time_up

    def alarm_handler(self, signum, frame):
        self.time_up = True

    def check(self):
        if self.time_up:
            raise TimeUp()


class TimeUp(Exception):
    pass


class DelayedSignal(object):
    """Context manager that delays a single signal call."""
    def __init__(self, signal_number):
        self.signal_number = signal_number

    def __enter__(self):
        self.signal_occured = False
        self.old_handler = signal.signal(self.signal_number, self.handler)

    def __exit__(self, exception_type, exception_value, traceback):
        self.signal_occured = False
        signal.signal(self.signal_number, self.old_handler)
        if self.signal_occured:
            self.old_handler(self.handler_signum, self.handler_frame)

    def handler(self, signum, frame):
        assert not self.signal_occured, "Can't delay multiple signals."
        self.signal_occured = True
        self.handler_signum = signum
        self.handler_frame = frame


class PlayerTimingMixin(object):
    def timed_init(self, start_clock, buffer_seconds=1):
        return AlarmContextManager(
            seconds=(start_clock.seconds - buffer_seconds))

    def timed_turn(self, buffer_seconds=1):
        return AlarmContextManager(
            seconds=(self.play_clock.seconds - buffer_seconds))


def first_action(game_state, role):
    actions = game_state.legal_actions(role)
    try:
        return next(actions)
    finally:
        actions.close()


class Legal(GamePlayer):
    """Plays the first legal move."""
    def get_move(self):
        return str(first_action(self.game_state, self.role))


def random_action(game_state, role, as_string):
    selected_action = None
    for i, action in enumerate(game_state.legal_actions(role)):
        if random.randint(0, i) == 0:
            selected_action = action
    return selected_action


class Random(GamePlayer):
    """Plays a random legal move."""
    def get_move(self):
        return str(random_action(game_state=self.game_state, role=self.role))


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

        own_moves = [
            action.get() for action
            in tuple(game_state.legal_actions(self.role, persistent=True))]
        assert own_moves
        random.shuffle(own_moves)  # Avoid bias in case of score ties.

        if not score_matters and len(own_moves) == 1:
            self.notify_trivial_turn()
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

            for other_roles_moves in itertools.product(
                    *other_roles_move_lists):
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

    def non_recursive_score_estimate_and_move_sequence(self, game_state,
                                                       depth):
        if game_state.is_terminal():
            return True, game_state.utility(self.role), ()
        return False, None, None

    def notify_trivial_turn(self):
        pass


class AlphaBeta(Minimax):
    """Runs Minimax algorithm with Alpha-Beta pruning to decide each move."""
    def min_step_break(self, score, max_step_score):
        return (score == self.min_utility or  # Can't get any lower.
                score <= max_step_score)  # Will be rejected by prev. max step.

    def max_step_break(self, score, min_step_score):
        return (score == self.max_utility or  # Can't get any higher.
                score >= min_step_score)  # Will be rejected by prev. min step.


class BoundedDepth(Minimax, PlayerTimingMixin):
    """Runs bounded depth search on each move."""

    PARAMETER_DESCRIPTIONS = OrderedDict([
        ('max_depth', ParameterDescription(
            type=int,
            help='Maximum search depth. -1 for iterative deepening.')),
        ('heuristic', ParameterDescription(
            type=str, choices=['zero', 'utility', 'mobility'],
            help='Heuristic method.')),
    ])

    def __init__(self, game, role, start_clock, play_clock, max_depth,
                 heuristic):
        super().__init__(game, role, start_clock, play_clock)
        self.max_depth = max_depth
        self.logger.debug('Max depth: {}'.format(max_depth))

        if callable(heuristic):
            self.heuristic_function = heuristic
        elif heuristic == 'zero':
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

    def non_recursive_score_estimate_and_move_sequence(self, game_state,
                                                       depth):
        if game_state.is_terminal():
            return True, game_state.utility(self.role), ()
        elif depth >= self.max_depth:
            # Scale the heuristic function to 10 - 90 so that
            # certain wins and losses carry more weight.
            return True, self.heuristic_function(game_state) * 0.8 + 10, ()
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

    def score_estimate_and_move_sequence(self,
                                         game_state,
                                         score_matters,
                                         depth,
                                         prev_min_step_score):
        self.timer.check()
        super().score_estimate_and_move_sequence(
            game_state=game_state, score_matters=score_matters,
            depth=depth, prev_min_step_score=prev_min_step_score)

    def get_move(self):
        if self.max_depth == -1:
            with self.timed_turn(buffer_seconds=2) as timer:
                self.timer = timer
                self.max_depth = 0
                self.trivial_turn = False
                action = first_action(self.game_state, self.role)
                try:
                    while True:
                        timer.check()
                        self.max_depth += 1
                        self.logger.debug(
                            'Running to depth {}'.format(self.max_depth))
                        action = super().get_move()
                        if self.trivial_turn:
                            break
                except TimeUp:
                    pass

            try:
                del self.timer
            except AttributeError:
                pass

            self.max_depth = -1
            return action

        else:
            return super().get_move()

    def notify_trivial_turn(self):
        self.trivial_turn = True


class GameSimulator(object):
    def __init__(self, role, roles):
        self.role = role
        self.roles = roles

    def play_random_game(self, game_state, timer):
        """Play a random game starting from `game_state`.

        Returns:
            The utility for `self.role` at the terminal state.
        """
        while not game_state.is_terminal():
            timer.check()
            game_state = game_state.apply_moves({
                role: random_action(game_state, role, as_string=False)
                for role in self.roles})

        return game_state.utility(self.role)


class MonteCarlo(BoundedDepth):
    """Runs bounded depth search with Monte Carlo heuristic."""

    PARAMETER_DESCRIPTIONS = OrderedDict([
        ('max_depth', BoundedDepth.PARAMETER_DESCRIPTIONS['max_depth']),
        ('num_probes', ParameterDescription(
            type=int,
            help='Number of probes to make once max_depth is reached.'))
    ])

    def __init__(self, game, role, start_clock, play_clock, max_depth,
                 num_probes):
        super().__init__(game=game, role=role, start_clock=start_clock,
                         play_clock=play_clock, max_depth=max_depth,
                         heuristic=self.heuristic_monte_carlo)
        self.game_simulator = GameSimulator(role=self.role, roles=self.roles)
        self.num_probes = num_probes

    def heuristic_monte_carlo(self, game_state):
        return (sum(self.probe(game_state) for _ in range(self.num_probes)) /
                self.num_probes)

    def probe(self, game_state):
        return self.game_simulator.play_random_game(game_state, self.timer)


class PartialMoveGameState(object):
    def __init__(self, game_state, roles=None, moves=None):
        self.game_state = game_state
        self._roles = (roles if roles is not None
                       else tuple(game_state.game.roles()))
        self._moves = moves if moves is not None else {}

    def apply_partial_move(self, role, action):
        assert role in self._roles
        assert role not in self._moves
        new_moves = self._moves.copy()
        new_moves[role] = action

        if len(new_moves) == len(self._roles):
            new_game_state = self.game_state.apply_moves(new_moves)
            new_moves = {}
        else:
            new_game_state = self.game_state

        return PartialMoveGameState(game_state=new_game_state,
                                    roles=self._roles,
                                    moves=new_moves)

    def apply_moves(self, moves):
        raise AttributeError('apply_moves')

    def __getattr__(self, name):
        return getattr(self.game_state, name)


class MonteCarloTreeSearch(GamePlayer, PlayerTimingMixin):
    """Monte-Carlo Tree Search

    Based on the Upper Confidence Bound 1 applied to Trees (UCT) algorithm.
    """

    PARAMETER_DESCRIPTIONS = OrderedDict([
        ('C', ParameterDescription(
            type=float, default=math.sqrt(2),
            help='Parameter controlling exploration rate. (default √2)'))
    ])

    def __init__(self, game, role, start_clock, play_clock, C):
        with self.timed_init(start_clock, buffer_seconds=2) as timer:
            super().__init__(game=game, role=role, start_clock=start_clock,
                             play_clock=play_clock)
            self.C = C
            self.role_index = self.roles.index(self.role)
            self.max_utility = self.game.max_utility()
            self.min_utility = self.game.min_utility()
            self.root = self._make_root_node()
            self.game_simulator = GameSimulator(
                role=self.role, roles=self.roles)

            try:
                while True:
                    timer.check()
                    self.run_search(timer)
            except TimeUp:
                pass

    def get_move(self):
        with self.timed_turn(buffer_seconds=3) as timer:
            try:
                while True:
                    timer.check()
                    self.run_search(timer)
            except TimeUp:
                pass

        for line in self._node_tree_lines(self.root, max_depth=2):
            self.logger.debug(line)

        x = list((action, child.mean_score())
                 for (action, child) in self.root.action_child.items()
                 if child.times_seen > 0)
        self.logger.debug(
            '{!s} - {!s}'.format(*max(x, key=operator.itemgetter(1))))
        return max(((action, child.mean_score())
                    for (action, child) in self.root.action_child.items()
                    if child.times_seen > 0),
                   key=operator.itemgetter(1))[0]

    def update_moves(self, new_moves):
        new_moves_dict = self._moves_dict(new_moves)
        super().update_moves(new_moves)

        while new_moves_dict:
            action = str(new_moves_dict.pop(self.root.role))

            try:
                self.root = self.root.action_child[action]
            except KeyError:
                self.root = self._make_root_node()
                break

        assert self.root.game_state == self.game_state

    def run_search(self, timer):
        node = self.root
        path = [node]

        # Select
        while not node.unseen_actions and node.action_child:
            timer.check()
            node = self.select_child(node)
            path.append(node)

        if node.game_state.is_terminal():
            self.backpropagate_terminal_node(path=path, node=node)
            return

        # Expand
        action = node.get_random_unseen_action()

        leaf_node = node.get_node_for_action(action)
        path.append(leaf_node)

        # Simulate
        score = self.simulate_game(leaf_node, timer)

        # Backpropagate
        node.attach_child(action=action, child=leaf_node)
        self.backpropagate_score(path=path, score=score)

    def node_game_state_score(self, node):
        return self.normalize_score(node.game_state_utility())

    def normalize_score(self, game_utility):
        """Convert game utility to a score in [0, 1]."""
        return ((game_utility - self.min_utility) /
                (self.max_utility - self.min_utility))

    def node_upper_confidence_bound(self, node, perspective_role,
                                    log_parent_times_seen):
        if perspective_role == self.role:
            score_factor = 1
        else:
            # Score is for self.role so other roles want it minimized
            score_factor = -1
        return (node.mean_score() * score_factor +
                self.C * math.sqrt(log_parent_times_seen / node.times_seen))

    def select_child(self, node):
        log_times_seen = math.log(node.times_seen)
        child_nodes = list(node.action_child.values())
        random.shuffle(child_nodes)
        return max(
            ((child, self.node_upper_confidence_bound(
                node=child,
                perspective_role=node.role,
                log_parent_times_seen=log_times_seen))
             for child in child_nodes),
            key=operator.itemgetter(1))[0]

    def simulate_game(self, node, timer):
        return self.normalize_score(self.game_simulator.play_random_game(
            node.game_state.game_state, timer))

    def backpropagate_terminal_node(self, path, node):
        score = self.node_game_state_score(node)
        self.backpropagate_score(path=path, score=score)
        # TODO: Also do Minimax backprop

    def backpropagate_score(self, path, score):
        for node in path:
            node.update(score_role=self.role, score=score)

    def _make_root_node(self):
        return self.Node(game_state=PartialMoveGameState(self.game_state),
                         role_index=self.role_index,
                         roles=self.roles)

    @staticmethod
    def _node_tree_lines(node, depth=0, max_depth=float('Inf')):
        indent = str(depth) + '  ' * depth
        yield indent + str(node)
        if depth + 1 > max_depth:
            raise StopIteration
        for action, child in node.action_child.items():
            yield indent + '>' + str(action)
            yield from MonteCarloTreeSearch._node_tree_lines(
                node=child, depth=(depth + 1), max_depth=max_depth)

    class Node(object):
        def __init__(self, game_state, role_index, roles):
            self.game_state = game_state
            self.role_index = role_index
            self.roles = roles
            self.role = roles[role_index]
            self.action_child = {}

            self.unseen_actions = self._get_unseen_actions()

            self.total_score = 0
            self.times_seen = 0

        def __str__(self):
            try:
                role_str = self.role_str
            except AttributeError:
                self.role_str = str(self.role)
                role_str = self.role_str

            try:
                mean_score = self.mean_score()
            except ZeroDivisionError:
                mean_score = float('NaN')

            return '{role!s} - {times_seen} - {mean_score}'.format(
                role=role_str, times_seen=self.times_seen,
                mean_score=mean_score)

        def mean_score(self):
            return self.total_score / self.times_seen

        def get_random_unseen_action(self):
            return self.unseen_actions[-1].get()

        def game_state_utility(self):
            return self.game_state.utility(self.role)

        def get_node_for_action(self, action):
            return MonteCarloTreeSearch.Node(
                game_state=self.game_state.apply_partial_move(
                    self.role, action),
                role_index=((self.role_index + 1) % len(self.roles)),
                roles=self.roles)

        def attach_child(self, action, child):
            action_string = str(action)
            assert action_string not in self.action_child
            assert action_string == str(self.unseen_actions[-1].get())
            self.action_child[action_string] = child
            self.unseen_actions.pop()

        def update(self, score_role, score):
            self.times_seen += 1
            self.total_score += score

        def _get_unseen_actions(self):
            unseen_actions = [
                action for action in self.game_state.legal_actions(self.role)
                if str(action) not in self.action_child]
            random.shuffle(unseen_actions)
            return unseen_actions

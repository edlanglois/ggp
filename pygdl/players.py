from collections import OrderedDict
import logging
import random

logger = logging.getLogger(__name__)


class PlayerFactory(object):
    """Player factory for PrologGamePlayer"""
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


class PrologGamePlayer(object):
    MIN_SCORE = 0
    MAX_SCORE = 100

    PARAMETER_DESCRIPTIONS = OrderedDict()

    def __init__(self, game, role, start_clock, play_clock):
        self.logger = logging.getLogger(__name__ + self.__class__.__name__)
        self.logger.info('Created {!s} with role "{!s}"'.format(
            self.__class__.__name__, role))
        self.game = game
        self.role = role
        self.play_clock = play_clock

        self.roles = tuple(self.game.roles())
        self.game_state = self.game.initial_state()

    @classmethod
    def player_name(cls):
        return cls.__class__.__name__

    def update_moves(self, new_moves):
        assert(len(self.roles) == len(new_moves))

        self.logger.debug("GAME DESCRIPTION FOR TURN %s",
                          self.game_state.turn_number())
        for base in self.game.base_terms():
            self.logger.debug("\t%s", str(base))

        moves = {role: move
                 for role, move in zip(self.roles, new_moves)}

        self.game_state = self.game_state.apply_moves(moves)

    def stop(self):
        self.logger.info('Stopping game. Terminal: {!s}. Score: {!s}'.format(
            self.game_state.is_terminal(),
            self.game_state.utility(self.role)))

    def abort(self):
        self.logger.info('Aborting game.')


class Legal(PrologGamePlayer):
    """Plays the first legal move."""
    def get_move(self):
        moves = self.game_state.legal_moves(self.role)
        first_move = next(moves)
        moves.close()
        return first_move


class Random(PrologGamePlayer):
    """Plays a random legal move."""
    def get_move(self):
        random_move = None
        for i, move in enumerate(self.game_state.legal_moves(self.role)):
            if random.randint(0, i) == 0:
                random_move = move

        return random_move


class SimpleDepthFirstSearch(PrologGamePlayer):
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        assert self.game_state.num_roles() == 1, \
            "SimpleDepthFirstSearch only works for single-player games."

    def get_best_move_sequence(self):
        _, move_sequence = self.get_best_score_and_move_sequence()
        return move_sequence

    def get_best_score_and_move_sequence(self):
        return self._get_best_score_and_move_sequence(
            game_state=self.game_state)

    def _get_best_score_and_move_sequence(self, game_state):
        if game_state.is_terminal():
            return game_state.utility(self.role), tuple()

        moves = tuple(game_state.legal_moves(self.role))

        best_score = self.MIN_SCORE - 1
        best_move_sequence = tuple()

        for move in moves:
            score, move_sequence = self.get_best_score_and_move_sequence(
                game_state=game_state.apply_moves((move)))

            assert score >= self.MIN_SCORE
            assert score <= self.MAX_SCORE

            if score > best_score:
                best_score = score
                best_move_sequence = (move,) + move_sequence

            if best_score == self.MAX_SCORE:
                break

        return best_score, best_move_sequence


class CompulsiveDeliberation(SimpleDepthFirstSearch):
    """For each move, find optimal move with DFS."""
    def get_move(self):
        move_sequence = self.get_best_move_sequence()
        return move_sequence[0]


class SequentialPlanner(SimpleDepthFirstSearch):
    """On init, find optimal move sequence with DFS. Save and replay it."""
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        move_sequence = self.get_best_move_sequence()
        self.move_sequence = list(move_sequence)

    def get_move(self):
        move = self.move_sequence.pop(0)
        return move


class SearchPlayer(PrologGamePlayer):
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        self.players = tuple(str(role_)
                             for role_ in self.game.roles())
        self.own_player_index = self.players.index(self.role)

    def succesor_player_index(self, player_index):
        return (player_index + 1) % len(self.players)

    def recursive_per_player_search(self, depth, player_index,
                                    *search_args, **search_kwargs):
        """Search in which one recursive call is made per player turn.

        It is assumed that this player's turn is first.
        Turns are taken just at the start of the recursive call corresponding
        to the current player's turn (except on the first call).
        """
        self.logger.debug("Search %s %s", depth, player_index)
        is_own_turn = player_index == self.own_player_index
        # TODO: Requires re-write

        if is_own_turn and depth > 0:
            mustUndoTurn = True
            self.logger.debug("Next turn")
            self.game_state.next_turn()
        else:
            mustUndoTurn = False
            if depth == 0:
                assert is_own_turn

        try:
            current_role = self.players[player_index]
            is_terminal = self.game_state.is_terminal()
            moves = tuple(self.game_state.legal_moves(current_role))
            return self.search_for_move(depth=depth,
                                        player_index=player_index,
                                        current_role=current_role,
                                        is_own_turn=is_own_turn,
                                        is_terminal=is_terminal,
                                        moves=moves,
                                        *search_args,
                                        **search_kwargs)

        finally:
            if mustUndoTurn:
                self.logger.debug("Undo turn")
                self.game_state.previous_turn()

    def move_and_recursive_search(self, move, depth, player_index,
                                  current_role, *search_args, **search_kwargs):
        """Make a move and return result of recursive_per_player_search

        Implementations of search_for_move should call this instead of directly
        calling recursive_per_player_search.
        """
        self.logger.debug("%s:\t%s", str(current_role), str(move))
        self.game_state.set_move(current_role, move)
        return self.recursive_per_player_search(
            depth=(depth + int(player_index == self.own_player_index)),
            player_index=self.succesor_player_index(player_index),
            *search_args,
            **search_kwargs)

    def get_current_state_utility(self):
        return self.game_state.get_utility(self.role)

    def get_best_move_without_search(self, moves, score_required):
        """Attemps to find the best move without search.

        Returns (found, move, score)
        found is true if a move was found.
        move and score are None if no move was found.
        score may be None even if a move was found.
        """
        assert moves
        if score_required and len(moves) == 0:
            return True, moves[0], None
        return False, None, None

    def search_for_move(self,
                        depth,
                        player_index,
                        current_role,
                        is_own_turn,
                        is_terminal,
                        moves,
                        *search_args,
                        **search_kwargs):
        raise NotImplementedError


class Minimax(SearchPlayer):
    """Runs Minimax algorithm to decide each move."""
    def search_for_move(self,
                        depth,
                        player_index,
                        current_role,
                        is_own_turn,
                        is_terminal,
                        moves,
                        score_required):
        if is_terminal:
            return self.get_current_state_utility(), None

        found, move, score = self.get_best_move_without_search(moves,
                                                               score_required)
        if found:
            return move, score

        if is_own_turn:
            best_score = float('-Inf')
            best_possible_score = self.MAX_SCORE

            def is_better_score(new, cur):
                return new > cur
        else:
            best_score = float('Inf')
            best_possible_score = self.MIN_SCORE

            def is_better_score(new, cur):
                return new < cur

        best_move = None
        for move in moves:
            score, _ = self.move_and_recursive_search(
                move=move,
                depth=depth,
                player_index=player_index,
                current_role=current_role,
                score_required=True
            )
            assert score >= self.MIN_SCORE
            assert score <= self.MAX_SCORE

            if is_better_score(score, best_score):
                best_score = score
                best_move = move

            if best_score == best_possible_score:
                break

        return best_score, best_move

    def get_move(self):
        _, move = self.recursive_per_player_search(
            depth=0,
            player_index=self.own_player_index,
            score_required=False)
        return move


class AlphaBeta(SearchPlayer):
    """Runs Minimax algorithm with Alpha-Beta pruning to decide each move."""
    def search_for_move(self,
                        depth,
                        player_index,
                        current_role,
                        is_own_turn,
                        is_terminal,
                        moves,
                        score_required,
                        alpha,
                        beta):
        if is_terminal:
            return self.get_current_state_utility(), None

        found, move, score = self.get_best_move_without_search(moves,
                                                               score_required)
        if found:
            return move, score

        if is_own_turn:
            best_score = float('-Inf')
            best_possible_score = self.MAX_SCORE

            def is_better_score(new, cur):
                return new > cur

            def update_alpha_beta(alpha, beta, best_score):
                return max(alpha, best_score), beta

        else:
            best_score = float('Inf')
            best_possible_score = self.MIN_SCORE

            def is_better_score(new, cur):
                return new < cur

            def update_alpha_beta(alpha, beta, best_score):
                return alpha, min(beta, best_score)

        best_move = None
        for move in moves:
            score, _ = self.move_and_recursive_search(
                move=move,
                depth=depth,
                player_index=player_index,
                current_role=current_role,
                score_required=score_required,
                alpha=alpha,
                beta=beta)
            assert score >= self.MIN_SCORE
            assert score <= self.MAX_SCORE

            if is_better_score(score, best_score):
                best_score = score
                best_move = move

                if score > best_score:
                    best_score = score
                    best_move = move
                    alpha, beta = update_alpha_beta(alpha, beta, best_score)

                if alpha >= beta:
                    break

                if best_score == best_possible_score:
                    break

        return best_score, best_move

    def get_move(self):
        _, move = self.recursive_per_player_search(
            depth=0,
            player_index=self.own_player_index,
            score_required=False,
            alpha=float('-Inf'),
            beta=float('Inf'))
        return move


class BoundedDepth(AlphaBeta):
    """Runs bounded depth search on each move."""

    PARAMETER_DESCRIPTIONS = OrderedDict([
        ('max_depth', ParameterDescription(
            type=int, help='Maximum search depth.')),
        ('heuristic', ParameterDescription(
            type=str, choices=['zero', 'utility', 'mobility'],
            help='Heuristic method.')),
    ])

    def __init__(self, game_state, role, start_clock, play_clock, max_depth,
                 heuristic):
        super().__init__(game_state, role, start_clock, play_clock)
        self.max_depth = max_depth
        self.heuristic = heuristic

        roles = list(self.game_state.get_roles())
        self.num_possible_moves = {
            str(role_): len(set(self.game_state.get_all_moves(role_)))
            for role_ in roles
        }

    def search_for_move(self,
                        depth,
                        player_index,
                        current_role,
                        is_own_turn,
                        is_terminal,
                        moves,
                        score_required,
                        alpha,
                        beta):

        if not is_terminal and depth > self.max_depth:
            return self.current_state_heuristic(), None
        else:
            return super().search_for_move(depth,
                                           player_index,
                                           current_role,
                                           is_own_turn,
                                           is_terminal,
                                           moves,
                                           score_required,
                                           alpha,
                                           beta)

    def current_state_heuristic(self):
        if self.heuristic == 'zero':
            h = self.heuristic_zero()
        elif self.heuristic == 'utility':
            h = self.heuristic_utility()
        elif self.heuristic == 'mobility':
            h = self.heuristic_mobility()
        else:
            raise AssertionError
        self.logger.debug("Heuristic: %s", h)
        return h

    def heuristic_zero(self):
        return 0

    def heuristic_utility(self):
        return self.game_state.get_utility(self.role)

    def heuristic_mobility(self):
        return (float(len(set(self.game_state.legal_moves(self.role)))) /
                self.num_possible_moves[str(self.role)])

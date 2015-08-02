import logging
import random

from pygdl.sexpr import to_s_expression_string

logger = logging.getLogger(__name__)


class PrologGamePlayer(object):
    MIN_SCORE = 0
    MAX_SCORE = 100

    def __init__(self, game_state, role, _start_clock, play_clock):
        self.logger = logging.getLogger(__name__ + self.__class__.__name__)
        self.logger.info('Created {!s} with role "{!s}"'.format(
            self.__class__.__name__, role))
        self.game_state = game_state
        self.role = role
        self.play_clock = play_clock

    @classmethod
    def player_name(cls):
        return cls.__class__.__name__

    def update_moves(self, new_moves):
        roles = list(self.game_state.get_roles())
        roles = list(self.game_state.get_roles())
        assert(len(roles) == len(new_moves))

        self.logger.debug("GAME DESCRIPTION FOR TURN %s",
                          self.game_state.get_turn())
        for base in self.game_state.get_state_terms():
            self.logger.debug("\t%s", str(base))

        for role, move in zip(roles, new_moves):
            self.game_state.set_move(role, to_s_expression_string(move))
        self.game_state.next_turn()

    def stop(self):
        self.logger.info('Stopping game. Terminal: {!s}. Score: {!s}'.format(
            self.game_state.is_terminal(),
            self.game_state.get_utility(self.role)))

    def abort(self):
        self.logger.info('Aborting game.')


class Legal(PrologGamePlayer):
    def get_move(self):
        moves = self.game_state.get_legal_moves(self.role)
        first_move = next(moves)
        moves.close()
        return str(first_move)


class Random(PrologGamePlayer):
    def get_move(self):
        random_move = None
        for i, move in enumerate(self.game_state.get_legal_moves(self.role)):
            if random.randint(0, i) == 0:
                random_move = move

        return str(random_move)


class SimpleDepthFirstSearch(PrologGamePlayer):
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        assert self.game_state.get_num_roles() == 1, \
            "CompulsiveDeliberation player only works for single-player games."

    def get_best_score_and_move_sequence(self):
        if self.game_state.is_terminal():
            return self.game_state.get_utility(self.role), tuple()

        moves = tuple(self.game_state.get_legal_moves(self.role))

        best_score = self.MIN_SCORE - 1
        best_move_sequence = tuple()
        for move in moves:
            self.game_state.set_move(self.role, move)
            self.game_state.next_turn()
            score, move_sequence = self.get_best_score_and_move_sequence()
            self.game_state.previous_turn()

            assert score >= self.MIN_SCORE
            assert score <= self.MAX_SCORE

            if score > best_score:
                best_score = score
                best_move_sequence = (move,) + move_sequence

            if best_score == self.MAX_SCORE:
                break

        return best_score, best_move_sequence


class CompulsiveDeliberation(SimpleDepthFirstSearch):
    def get_move(self):
        _, move_sequence = self.get_best_score_and_move_sequence()
        return str(move_sequence[0])


class SequentialPlanner(SimpleDepthFirstSearch):
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        _, move_sequence = self.get_best_score_and_move_sequence()
        self.move_sequence = list(move_sequence)

    def get_move(self):
        move = self.move_sequence[0]
        self.move_sequence.pop(0)
        return str(move)


class Minimax(PrologGamePlayer):
    def __init__(self, game_state, role, start_clock, play_clock):
        super().__init__(game_state, role, start_clock, play_clock)
        self.players = tuple(str(role_)
                             for role_ in self.game_state.get_roles())
        self.own_player_index = self.players.index(self.role)

    def succesor_player_index(self, player_index):
        return (player_index + 1) % len(self.players)

    def get_extreme_score_and_move(self, player_index, initial_call=True):
        self.logger.debug("Search %s %s", player_index, initial_call)
        if not initial_call and player_index == self.own_player_index:
            mustUndoTurn = True
            self.logger.debug("Next turn")
            self.game_state.next_turn()
        else:
            mustUndoTurn = False

        try:
            if self.game_state.is_terminal():
                return self.game_state.get_utility(self.role), None

            current_role = self.players[player_index]
            moves = tuple(self.game_state.get_legal_moves(current_role))

            if player_index == self.own_player_index:
                best_score = self.MIN_SCORE - 1
                best_move = None
                best_possible_score = self.MAX_SCORE

                def is_better_score(new, cur):
                    return new > cur
            else:
                best_score = self.MAX_SCORE + 1
                best_move = None
                best_possible_score = self.MIN_SCORE

                def is_better_score(new, cur):
                    return new < cur

            for move in moves:
                self.logger.debug("%s:\t%s", str(current_role), str(move))
                self.game_state.set_move(current_role, move)
                score, _ = self.get_extreme_score_and_move(
                    self.succesor_player_index(player_index),
                    initial_call=False)

                assert score >= self.MIN_SCORE
                assert score <= self.MAX_SCORE

                if is_better_score(score, best_score):
                    best_score = score
                    best_move = move

                if best_score == best_possible_score:
                    break

            return best_score, best_move

        finally:
            if mustUndoTurn:
                self.logger.debug("Undo turn")
                self.game_state.previous_turn()

    def get_move(self):
        _, move = self.get_extreme_score_and_move(self.own_player_index,
                                                  initial_call=True)
        return str(move)

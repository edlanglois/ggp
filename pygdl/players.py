import logging
import random

from pygdl.sexpr import to_s_expression_string

logger = logging.getLogger(__name__)


class PrologGamePlayer(object):
    def __init__(self, game_state, role, play_clock):
        self.logger = logging.getLogger(__name__ + self.__class__.__name__)
        self.logger.info('Created {!s} with role "{!s}"'.format(
            self.__class__.__name__, role))
        self.game_state = game_state
        self.role = role
        self.play_clock = play_clock


    def update_moves(self, new_moves):
        roles = list(self.game_state.get_roles())
        roles = list(self.game_state.get_roles())
        assert(len(roles) == len(new_moves))

        self.logger.debug("GAME DESCRIPTION FOR TURN %s",
                          self.game_state.get_turn())
        for base in self.game_state.get_state_terms():
            self.logger.debug("\t%s", str(base))

        for role, move in zip(roles, new_moves):
            # TODO: Remove str(...)
            self.game_state.set_move(str(role), to_s_expression_string(move))
        self.game_state.next_turn()

    def stop(self):
        self.logger.info('Stopping game. Terminal: {!s}'.format(
            self.game_state.is_terminal()))

    def abort(self):
        self.logger.info('Aborting game.')


class LegalGamePlayer(PrologGamePlayer):
    player_name = 'LegalGamePlayer'

    def __init__(self, game_state, role, _, play_clock):
        super().__init__(game_state, role, play_clock)

    def get_move(self):
        moves = self.game_state.get_legal_moves(self.role)
        first_move = next(moves)
        moves.close()
        return str(first_move)


class RandomGamePlayer(PrologGamePlayer):
    player_name = 'RandomGamePlayer'

    def __init__(self, game_state, role, _, play_clock):
        super().__init__(game_state, role, play_clock)

    def get_move(self):
        random_move = None
        for i, move in enumerate(self.game_state.get_legal_moves(self.role)):
            if random.randint(0, i) == 0:
                random_move = move

        return str(random_move)

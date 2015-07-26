import logging

logger = logging.getLogger(__name__)

from pygdl.kif import kif_s_expr_to_prolog

class PrologGamePlayer(object):
    def __init__(self, game_state, role, play_clock):
        logger.info('Created {!s} with role "{!s}"'.format(
            self.__class__.__name__, role))
        self.game_state = game_state
        self.role = role
        self.play_clock = play_clock

    def update_moves(self, new_moves):
        # TODO: remove str(...) and kif_s_expr_to_prolog(...)
        roles = list(self.game_state.get_roles())
        assert(len(roles) == len(new_moves))
        for role, move in zip(roles, new_moves):
            self.game_state.set_move(str(role), kif_s_expr_to_prolog(move))
        self.game_state.next_turn()

    def stop(self):
        logger.info('Stopping game. Terminal: {!s}'.format(
            self.game_state.is_terminal()))

    def abort(self):
        logger.info('Aborting game.')


class LegalGamePlayer(PrologGamePlayer):
    player_name = 'LegalGamePlayer'

    def __init__(self, game_state, role, _, play_clock):
        super().__init__(game_state, role, play_clock)

    def get_move(self):
        # TODO: ability to close queryies
        legal_moves = list(self.game_state.get_legal_moves(self.role))
        first_legal_move = legal_moves[0]

        return str(first_legal_move)

import faulthandler
import os.path
import os

from nose.tools import (
    assert_equal,
    assert_is_instance,
    assert_set_equal,
)
import nosepipe

from pygdl.gamestate import (
    GeneralGameManager,
    GeneralGame,
    GeneralGameState,
)

faulthandler.enable()
MODULE_DIR = os.path.dirname(os.path.relpath(__file__))
BUTTONS_AND_LIGHTS_FILE = os.path.join(MODULE_DIR, 'buttonsandlights.pl')


@nosepipe.isolate
def test_general_game_manager():
    print('\ngm:', os.getpid())
    ggm = GeneralGameManager()
    assert not ggm.game_exists('buttonsandlights')

    with open(BUTTONS_AND_LIGHTS_FILE, 'r') as f:
        rules = [line.strip() for line in f.readlines()]

    ggm.create_game('buttonsandlights', rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)
    assert not ggm.game_exists('buttons')

    # Re-create game
    ggm.create_game('buttonsandlights', rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)


def make_game_manager_with_buttons_and_lights():
    with open(BUTTONS_AND_LIGHTS_FILE, 'r') as f:
        rules = [line.strip() for line in f.readlines()]

    ggm = GeneralGameManager()
    ggm.create_game('buttonsandlights', rules)
    return ggm


class TestGeneralGame(object):
    def setUp(self):
        ggm = make_game_manager_with_buttons_and_lights()
        self.game = GeneralGame(ggm, 'buttonsandlights')

    def robot_role(self):
        return self.game.role_object('robot')

    def test_initial_state(self):
        assert_is_instance(self.game.initial_state(), GeneralGameState)

    def test_roles(self):
        assert_set_equal({str(role) for role in self.game.roles()}, {'robot'})

    def test_num_roles(self):
        assert_equal(self.game.num_roles(), 1)

    def test_role_object(self):
        role_object = self.game.role_object('robot')
        list(self.game.all_moves(role_object))

    def test_all_moves(self):
        assert_set_equal(
            {str(move) for move in self.game.all_moves(self.robot_role())},
            {'a', 'b', 'c'})

    def test_base_terms(self):
        assert_set_equal(
            {str(term) for term in self.game.base_terms()},
            {'1', '2', '3', '4', '5', '6', '7', 'p', 'q', 'r'})

    def test_max_utility(self):
        assert_equal(self.game.max_utility(), 100)

    def test_min_utility(self):
        assert_equal(self.game.min_utility(), 0)


class TestGeneralGameStateInitial(object):
    def setUp(self):
        ggm = make_game_manager_with_buttons_and_lights()
        self.game = GeneralGame(ggm, 'buttonsandlights')
        self.role = self.game.role_object('robot')
        self.initial_state = self.game.initial_state()

    def test_turn_number(self):
        assert_equal(self.initial_state.turn_number(), 0)

    def test_utility(self):
        assert_equal(self.initial_state.utility(self.role), 0)

    def test_legal_moves(self):
        assert_set_equal(
            {str(move) for move in self.initial_state.legal_moves(self.role)},
            {'a', 'b', 'c'})

    def test_state_terms(self):
        assert_set_equal(
            {str(term) for term in self.initial_state.state_terms()},
            {'1'})

    def test_is_terminal(self):
        assert_equal(self.initial_state.is_terminal(), False)

    def test_apply_moves(self):
        action = self.game.action_object('a')
        new_state = self.initial_state.apply_moves({self.role: action})

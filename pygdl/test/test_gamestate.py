import faulthandler
import os.path
import os

from nose.tools import assert_is_instance, assert_equal
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


class TestGeneralGame():
    def setUp(self):
        ggm = make_game_manager_with_buttons_and_lights()
        self.game = GeneralGame(ggm, 'buttonsandlights')

    def test_initial_state(self):
        assert_is_instance(self.game.initial_state(), GeneralGameState)

    def test_roles(self):
        assert_equal([str(role) for role in self.game.roles()], ['robot'])

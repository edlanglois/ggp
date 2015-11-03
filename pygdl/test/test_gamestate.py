import faulthandler
import os.path
import os

from nose.tools import (
    assert_equal,
    assert_is_instance,
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
TIC_TAC_TOE_FILE = os.path.join(MODULE_DIR, 'tictactoe.pl')


@nosepipe.isolate
def test_general_game_manager():
    ggm = GeneralGameManager()
    assert not ggm.game_exists('buttonsandlights')

    with open(BUTTONS_AND_LIGHTS_FILE, 'r') as f:
        buttons_and_lights_rules = [line.strip() for line in f.readlines()]

    ggm.create_game('buttonsandlights', buttons_and_lights_rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)
    assert not ggm.game_exists('buttons')

    # Re-create game
    ggm.create_game('buttonsandlights', buttons_and_lights_rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)

    with open(TIC_TAC_TOE_FILE, 'r') as f:
        tic_tac_toe_rules = [line.strip() for line in f.readlines()]

    # Create a new game
    ggm.create_game('tictactoe', tic_tac_toe_rules)
    assert ggm.game_exists('tictactoe')
    assert_is_instance(ggm.game('tictactoe'), GeneralGame)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)


def make_game_manager(game_name, rules_file):
    with open(rules_file, 'r') as f:
        rules = [line.strip() for line in f.readlines()]

    ggm = GeneralGameManager()
    ggm.create_game(game_name, rules)
    return ggm


class BaseTestGeneralGame(object):
    def __init__(self, game_name, game_rules_file, roles, actions, base_terms):
        self.game_name = game_name
        self.game_rules_file = game_rules_file
        self.roles = roles
        if isinstance(actions, dict):
            self.actions = actions
        else:
            self.actions = {role: actions for role in self.roles}
        self.base_terms = base_terms

    def setUp(self):
        self.ggm = make_game_manager(self.game_name, self.game_rules_file)
        self.game = GeneralGame(self.ggm, self.game_name)

    def test_init(self):
        assert_equal(self.game.game_manager, self.ggm)
        assert_equal(str(self.game.game_id), self.game_name)

    def test_initial_state(self):
        assert_is_instance(self.game.initial_state(), GeneralGameState)

    def test_roles(self):
        assert_equal({str(role) for role in self.game.roles()}, self.roles)

    def test_num_roles(self):
        assert_equal(self.game.num_roles(), len(self.roles))

    def test_role_object(self):
        for role in self.roles:
            role_object = self.game.role_object(role)
            assert_equal(str(role_object), role)
            list(self.game.all_moves(role_object))

    def test_action_object(self):
        action = next(iter(next(iter(self.actions.values()))))
        action_object = self.game.action_object(action)
        assert_equal(str(action_object), action)

    def test_all_moves(self):
        for role in self.roles:
            role_object = self.game.role_object(role)
            assert_equal(
                {str(move) for move in self.game.all_moves(role_object)},
                self.actions[role])

    def test_base_terms(self):
        assert_equal(
            {str(term) for term in self.game.base_terms()},
            self.base_terms)

    def test_max_utility(self):
        assert_equal(self.game.max_utility(), 100)

    def test_min_utility(self):
        assert_equal(self.game.min_utility(), 0)


class TestGeneralGameButtonsAndLights(BaseTestGeneralGame):
    def __init__(self):
        super(TestGeneralGameButtonsAndLights, self).__init__(
            game_name='buttonsandlights',
            game_rules_file=BUTTONS_AND_LIGHTS_FILE,
            roles={'robot'},
            actions={'a', 'b', 'c'},
            base_terms={'1', '2', '3', '4', '5', '6', '7', 'p', 'q', 'r'})


class TestGeneralGameTicTacToe(BaseTestGeneralGame):
    def __init__(self):
        super(TestGeneralGameTicTacToe, self).__init__(
            game_name='tictactoe',
            game_rules_file=TIC_TAC_TOE_FILE,
            roles={'white', 'black'},
            actions={'mark({},{})'.format(i, j)
                     for i in range(1, 4) for j in range(1, 4)},
            base_terms=(
                {'step({})'.format(i) for i in range(1, 8)}.union(
                {'cell({},{},{})'.format(i, j, x)
                 for i in range(1, 4) for j in range(1, 4) for x in 'xob'})))


class TestGeneralGameStateButtonsAndLights(object):
    def setUp(self):
        ggm = make_game_manager('buttonsandlights', BUTTONS_AND_LIGHTS_FILE)
        self.game = GeneralGame(ggm, 'buttonsandlights')
        self.role = self.game.role_object('robot')
        self.initial_state = self.game.initial_state()

    def test_turn_number(self):
        assert_equal(self.initial_state.turn_number(), 0)

    def test_utility(self):
        assert_equal(self.initial_state.utility(self.role), 0)

    def test_legal_moves(self):
        assert_equal(
            {str(move) for move in self.initial_state.legal_moves(self.role)},
            {'a', 'b', 'c'})

    def test_state_terms(self):
        assert_equal(
            {str(term) for term in self.initial_state.state_terms()},
            {'1'})

    def test_is_terminal(self):
        assert_equal(self.initial_state.is_terminal(), False)

    def test_game_id(self):
        assert_equal(str(self.initial_state.game_id()), 'buttonsandlights')

    def test_apply_moves_once(self):
        action = self.game.action_object('a')
        new_state = self.initial_state.apply_moves({self.role: action})

        assert_equal(new_state.turn_number(), 1)
        assert_equal(new_state.utility(self.role), 0)
        assert_equal(
            {str(move) for move in new_state.legal_moves(self.role)},
            {'a', 'b', 'c'})
        assert_equal(
            {str(term) for term in new_state.state_terms()},
            {'2', 'p'})
        assert_equal(new_state.is_terminal(), False)

    def test_apply_moves_check_initial(self):
        action = self.game.action_object('a')
        self.initial_state.apply_moves({self.role: action})

        # Check that the initial state is unchanged
        assert_equal(self.initial_state.turn_number(), 0)
        assert_equal(self.initial_state.utility(self.role), 0)
        assert_equal(
            {str(move) for move in self.initial_state.legal_moves(self.role)},
            {'a', 'b', 'c'})
        assert_equal(
            {str(term) for term in self.initial_state.state_terms()},
            {'1'})
        assert_equal(self.initial_state.is_terminal(), False)

    def test_apply_moves_full_game_won(self):
        a = self.game.action_object('a')
        b = self.game.action_object('b')
        c = self.game.action_object('c')
        final_state = self.initial_state.apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: c}).apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: a})

        assert_equal(final_state.turn_number(), 6)
        assert_equal(final_state.utility(self.role), 100)
        assert_equal(
            {str(move) for move in final_state.legal_moves(self.role)},
            {'a', 'b', 'c'})
        assert_equal(
            {str(term) for term in final_state.state_terms()},
            {'7', 'p', 'q', 'r'})
        assert_equal(final_state.is_terminal(), True)

    def test_apply_moves_full_game_won(self):
        a = self.game.action_object('a')
        b = self.game.action_object('b')
        c = self.game.action_object('c')
        final_state = self.initial_state.apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: c}).apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: b})

        assert_equal(final_state.turn_number(), 6)
        assert_equal(final_state.utility(self.role), 0)
        assert_equal(
            {str(move) for move in final_state.legal_moves(self.role)},
            {'a', 'b', 'c'})
        assert_equal(
            {str(term) for term in final_state.state_terms()},
            {'7', 'p', 'r'})
        assert_equal(final_state.is_terminal(), True)

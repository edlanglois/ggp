import faulthandler
import itertools
import os
import os.path

from nose.tools import (
    assert_equal,
    assert_false,
    assert_is_instance,
    assert_true,
)
import nosepipe

from ggp.gamestate import (
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

    def test_roles_iterating(self):
        assert_equal(sorted([str(role) for role in self.game.roles()]),
                     sorted(list(self.roles)))

    def test_roles_not_iterating(self):
        assert_equal(sorted([str(role) for role in list(self.game.roles())]),
                     sorted(list(self.roles)))

    def test_num_roles(self):
        assert_equal(self.game.num_roles(), len(self.roles))

    def test_role_object(self):
        for role in self.roles:
            role_object = self.game.role_object(role)
            assert_equal(str(role_object), role)
            list(self.game.all_actions(role_object, persistent=False))

    def test_action_object(self):
        action = next(iter(next(iter(self.actions.values()))))
        action_object = self.game.action_object(action)
        assert_equal(str(action_object), action)

    def test_all_actions_iterating(self):
        for role in self.roles:
            role_object = self.game.role_object(role)
            assert_equal(
                sorted([str(move) for move
                        in self.game.all_actions(role_object,
                                                 persistent=False)]),
                sorted(list(self.actions[role])))

    def test_all_actions_not_iterating(self):
        for role in self.roles:
            role_object = self.game.role_object(role)
            assert_equal(
                sorted([str(move.get()) for move
                        in list(self.game.all_actions(role_object,
                                                      persistent=True))]),
                sorted(list(self.actions[role])))

    def test_base_terms_iterating(self):
        assert_equal(
            sorted([str(term) for term
                    in self.game.base_terms(persistent=False)]),
            sorted(list(self.base_terms)))

    def test_base_terms_not_iterating(self):
        assert_equal(
            sorted([str(term.get()) for term
                    in list(self.game.base_terms(persistent=True))]),
            sorted(list(self.base_terms)))

    def test_max_utility(self):
        assert_equal(self.game.max_utility(), 100)

    def test_min_utility(self):
        assert_equal(self.game.min_utility(), 0)


class TestGeneralGameButtonsAndLights(BaseTestGeneralGame):
    def __init__(self):
        super(TestGeneralGameButtonsAndLights, self).__init__(
            game_name='buttonsandlights',
            game_rules_file=BUTTONS_AND_LIGHTS_FILE,
            roles=['robot'],
            actions=['a', 'b', 'c'],
            base_terms=['1', '2', '3', '4', '5', '6', '7', 'p', 'q', 'r'])


class TestGeneralGameTicTacToe(BaseTestGeneralGame):
    def __init__(self):
        super(TestGeneralGameTicTacToe, self).__init__(
            game_name='tictactoe',
            game_rules_file=TIC_TAC_TOE_FILE,
            roles=['white', 'black'],
            actions=['mark({},{})'.format(i, j)
                     for i in range(1, 4) for j in range(1, 4)],
            base_terms=(
                ['step({})'.format(i) for i in range(1, 8)] +
                ['cell({},{},{})'.format(i, j, x)
                 for i in range(1, 4) for j in range(1, 4) for x in 'xob'])
        )


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

    def test_legal_actions_iterating(self):
        assert_equal(
            sorted([str(move) for move
                    in self.initial_state.legal_actions(self.role,
                                                        persistent=False)]),
            sorted(['a', 'b', 'c']))

    def test_legal_actions_not_iterating(self):
        assert_equal(
            sorted([str(move.get()) for move
                    in list(self.initial_state.legal_actions(
                        self.role, persistent=True))]),
            sorted(['a', 'b', 'c']))

    def test_state_terms_iterating(self):
        assert_equal(
            sorted([str(term) for term
                    in self.initial_state.state_terms(persistent=False)]),
            sorted(['1']))

    def test_state_terms_not_iterating(self):
        assert_equal(
            sorted([str(term.get()) for term
                    in list(self.initial_state.state_terms(persistent=True))]),
            sorted(['1']))

    def test_is_terminal(self):
        assert_false(self.initial_state.is_terminal())

    def test_game_id(self):
        assert_equal(str(self.initial_state.game_id()), 'buttonsandlights')

    def test_apply_moves_once(self):
        action = self.game.action_object('a')
        new_state = self.initial_state.apply_moves({self.role: action})

        assert_equal(new_state.turn_number(), 1)
        assert_equal(new_state.utility(self.role), 0)
        assert_equal(
            sorted([str(move) for move
                    in new_state.legal_actions(self.role, persistent=False)]),
            sorted(['a', 'b', 'c']))
        assert_equal(
            sorted([str(term) for term
                    in new_state.state_terms(persistent=False)]),
            sorted(['2', 'p']))
        assert_false(new_state.is_terminal())

    def test_apply_moves_check_initial(self):
        action = self.game.action_object('a')
        self.initial_state.apply_moves({self.role: action})

        # Check that the initial state is unchanged
        assert_equal(self.initial_state.turn_number(), 0)
        assert_equal(self.initial_state.utility(self.role), 0)
        assert_equal(
            sorted([str(move) for move
                    in self.initial_state.legal_actions(self.role,
                                                        persistent=False)]),
            sorted(['a', 'b', 'c']))
        assert_equal(
            sorted([str(term) for term
                    in self.initial_state.state_terms(persistent=False)]),
            sorted(['1']))
        assert_false(self.initial_state.is_terminal())

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
            sorted([str(move) for move
                    in final_state.legal_actions(self.role, persistent=False)]),
            sorted(['a', 'b', 'c']))
        assert_equal(
            sorted([str(term) for term
                    in final_state.state_terms(persistent=False)]),
            sorted(['7', 'p', 'q', 'r']))
        assert_true(final_state.is_terminal())

    def test_apply_moves_full_game_lost(self):
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
            sorted([str(move) for move
                    in final_state.legal_actions(self.role, persistent=False)]),
            sorted(['a', 'b', 'c']))
        assert_equal(
            sorted([str(term) for term
                    in final_state.state_terms(persistent=False)]),
            sorted(['7', 'p', 'r']))
        assert_true(final_state.is_terminal())


def test_play_tic_tac_toe():
    ggm = make_game_manager('tictactoe', TIC_TAC_TOE_FILE)
    game = ggm.game('tictactoe')
    state0 = game.initial_state()

    black = game.role_object('black')
    white = game.role_object('white')
    actions = {i: {j: game.action_object("mark('{}', '{}')".format(i, j))
                   for j in range(1, 4)}
               for i in range(1, 4)}
    assert_equal({str(action) for action
                  in game.all_actions(white, persistent=False)},
                 set(itertools.chain(
                     *((str(action) for action in value.values())
                       for value in actions.values()))))

    assert_equal(state0.turn_number(), 0)
    assert_equal(state0.utility(white), 50)
    assert_equal(state0.utility(black), 50)
    assert_false(state0.is_terminal())
    assert_equal(sorted([str(term) for term
                         in state0.state_terms(persistent=False)]),
                 sorted(['cell({},{},b)'.format(i, j)
                         for i in range(1, 4) for j in range(1, 4)] +
                        ['step(1)']))

    state1 = state0.apply_moves({black: actions[2][2], white: actions[2][3]})
    state2 = state1.apply_moves({black: actions[1][2], white: actions[1][3]})
    state3 = state2.apply_moves({black: actions[2][1], white: actions[3][1]})

    assert_equal(state3.turn_number(), 3)
    assert_equal(state3.utility(white), 50)
    assert_equal(state3.utility(black), 50)
    assert_false(state3.is_terminal())
    assert_equal(
        sorted([str(action) for action
                in state3.legal_actions(white, persistent=False)]),
        sorted(["mark({},{})".format(i, j)
                for i, j in [(1, 1), (3, 2), (3, 3)]]))

    state4_won = state3.apply_moves({black: actions[3][2],
                                     white: actions[1][1]})
    assert_equal(state4_won.turn_number(), 4)
    assert_equal(state4_won.utility(white), 0)
    assert_equal(state4_won.utility(black), 100)
    assert_true(state4_won.is_terminal())

    state4_tie = state3.apply_moves({black: actions[3][3],
                                     white: actions[1][1]})
    assert_equal(state4_tie.turn_number(), 4)
    assert_equal(state4_tie.utility(white), 50)
    assert_equal(state4_tie.utility(black), 50)
    assert_false(state4_tie.is_terminal())

    # Make sure state4_won is still valid
    assert_equal(state4_won.turn_number(), 4)
    assert_equal(state4_won.utility(white), 0)
    assert_equal(state4_won.utility(black), 100)
    assert_true(state4_won.is_terminal())

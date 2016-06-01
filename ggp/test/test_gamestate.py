import faulthandler
import itertools
import os
import os.path

from nose.tools import (
    assert_equal,
    assert_false,
    assert_is_instance,
    assert_not_equal,
    assert_regex,
    assert_true,
)
import nosepipe

from ggp.gamestate import (
    GeneralGameManager,
    GeneralGame,
    GeneralGameState,
    Action,
    Role,
    GameProposition,
)

faulthandler.enable()
MODULE_DIR = os.path.dirname(os.path.relpath(__file__))
BUTTONS_AND_LIGHTS_FILE = os.path.join(MODULE_DIR, 'buttonsandlights.gdl')
TIC_TAC_TOE_FILE = os.path.join(MODULE_DIR, 'tictactoe.gdl')
ALQUERQUE_FILE = os.path.join(MODULE_DIR, 'alquerque.gdl')


def test_role__str__():
    assert_equal(str(Role('foo')), 'foo')


def test_role__eq__():
    assert_equal(Role('foo'), Role('foo'))
    assert_not_equal(Role('foo'), Role('bar'))


def test_action__str__():
    assert_equal(str(Action('(foo bar)')), '(foo bar)')
    assert_equal(str(Action('foo')), 'foo')


def test_action__eq__():
    assert_equal(Action('foo'), Action('foo'))
    assert_not_equal(Action('foo'), Action('bar'))


def test_game_proposition__str__():
    assert_regex(
        str(GameProposition('(baz (foo ?x) (bar ?x))')),
        r'\(baz \(foo (\?[_A-Z][_A-Za-z0-9]*)\) \(bar \1\)\)')


@nosepipe.isolate
def test_general_game_manager():
    ggm = GeneralGameManager()
    assert not ggm.game_exists('buttonsandlights')

    with open(BUTTONS_AND_LIGHTS_FILE, 'r') as f:
        buttons_and_lights_rules = '\n'.join(line.strip() for line in
                                             f.readlines())

    ggm.create_game('buttonsandlights', buttons_and_lights_rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)
    assert not ggm.game_exists('buttons')

    # Re-create game
    ggm.create_game('buttonsandlights', buttons_and_lights_rules)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)

    with open(TIC_TAC_TOE_FILE, 'r') as f:
        tic_tac_toe_rules = '\n'.join(line.strip() for line in f.readlines())

    # Create a new game
    ggm.create_game('tictactoe', tic_tac_toe_rules)
    assert ggm.game_exists('tictactoe')
    assert_is_instance(ggm.game('tictactoe'), GeneralGame)
    assert ggm.game_exists('buttonsandlights')
    assert_is_instance(ggm.game('buttonsandlights'), GeneralGame)


def make_game_manager(game_name, rules_file):
    with open(rules_file, 'r') as f:
        rules = '\n'.join(line for line
                          in (line.strip() for line in f.readlines())
                          if line and not line.startswith(';'))

    ggm = GeneralGameManager()
    ggm.create_game(game_name, rules)
    return ggm


def assert_object_sets_equal(a, b):
    assert_equal({str(obj): obj for obj in a}, {str(obj): obj for obj in b})


class BaseTestGeneralGame():
    def __init__(self, game_name, game_rules_file, roles, actions,
                 base_propositions):
        self.game_name = game_name
        self.game_rules_file = game_rules_file
        self.roles = [Role(role) for role in roles]
        if actions is not None:
            actions = [Action(action) for action in actions]
        if actions is None or isinstance(actions, dict):
            self.actions = actions
        else:
            self.actions = {role: actions for role in self.roles}
        self.base_propositions = [GameProposition(prop)
                                  for prop in base_propositions]

    def setUp(self):
        self.ggm = make_game_manager(self.game_name, self.game_rules_file)
        self.game = GeneralGame(self.ggm, self.game_name)

    def test_init(self):
        assert_equal(self.game.game_manager, self.ggm)
        assert_equal(str(self.game.game_id), self.game_name)

    def test_initial_state(self):
        assert_is_instance(self.game.initial_state(), GeneralGameState)

    def test_roles_iterating(self):
        assert_object_sets_equal(self.game.roles(), self.roles)

    def test_roles_not_iterating(self):
        assert_object_sets_equal(list(self.game.roles()), self.roles)

    def test_num_roles(self):
        assert_equal(self.game.num_roles(), len(self.roles))

    def test_roles(self):
        for role in self.roles:
            assert_equal(Role(str(role)), role)

    def test_action(self):
        if self.actions is None:
            return
        seen_actions = set()
        for action_list in self.actions.values():
            for action in action_list:
                action_str = str(action)
                if action_str in seen_actions:
                    continue
                seen_actions.add(action_str)
                assert_equal(Action(action_str), action)

    def test_all_actions_iterating(self):
        if self.actions is None:
            return
        for role in self.roles:
            assert_object_sets_equal(self.game.all_actions(role),
                                     self.actions[role])

    def test_all_actions_not_iterating(self):
        if self.actions is None:
            return
        for role in self.roles:
            assert_object_sets_equal(list(self.game.all_actions(role)),
                                     self.actions[role])

    def test_base_propositions_iterating(self):
        assert_object_sets_equal(self.game.base_propositions(),
                                 self.base_propositions)

    def test_base_propositions_not_iterating(self):
        assert_object_sets_equal(list(self.game.base_propositions()),
                                 self.base_propositions)

    def test_max_utility(self):
        assert_equal(self.game.max_utility(), 100)

    def test_min_utility(self):
        assert_equal(self.game.min_utility(), 0)


class TestGeneralGameButtonsAndLights(BaseTestGeneralGame):
    def __init__(self):
        super().__init__(
            game_name='buttonsandlights',
            game_rules_file=BUTTONS_AND_LIGHTS_FILE,
            roles=['robot'],
            actions=['a', 'b', 'c'],
            base_propositions=['1', '2', '3', '4', '5', '6', '7', 'p', 'q',
                               'r'])


class TestGeneralGameTicTacToe(BaseTestGeneralGame):
    def __init__(self):
        super().__init__(
            game_name='tictactoe',
            game_rules_file=TIC_TAC_TOE_FILE,
            roles=['white', 'black'],
            actions=['(mark {} {})'.format(i, j)
                     for i in range(1, 4) for j in range(1, 4)],
            base_propositions=(
                ['(step {})'.format(i) for i in range(1, 8)] +
                ['(cell {} {} {})'.format(i, j, x)
                 for i in range(1, 4) for j in range(1, 4) for x in 'xob'])
        )


class TestGeneralGameAlquerque(BaseTestGeneralGame):
    def __init__(self):
        super().__init__(
            game_name='alquerque',
            game_rules_file=ALQUERQUE_FILE,
            roles=['red', 'black'],
            actions=None,
            base_propositions=(
                ['(cell {} {} {})'.format(m, n, mark)
                 for m in range(1, 6) for n in range(1, 6)
                 for mark in ('black', 'red', 'blank')] +
                ['(score {} {})'.format(role, score * 10)
                 for role in ('red', 'black') for score in range(11)] +
                ['(control {})'.format(role) for role in ('red', 'black')] +
                ['(step {})'.format(step) for step in range(1, 31)])
        )


class TestGeneralGameStateButtonsAndLights():
    def setUp(self):
        ggm = make_game_manager('buttonsandlights', BUTTONS_AND_LIGHTS_FILE)
        self.game = GeneralGame(ggm, 'buttonsandlights')
        self.role = Role('robot')
        self.initial_state = self.game.initial_state()
        # Legal actions for all game states and roles.
        self.legal_actions = [Action(action) for action in 'abc']

    def test_turn_number(self):
        assert_equal(self.initial_state.turn_number(), 0)

    def test_utility(self):
        assert_equal(self.initial_state.utility(self.role), 0)

    def test_legal_actions_iterating(self):
        assert_object_sets_equal(self.initial_state.legal_actions(self.role),
                                 self.legal_actions)

    def test_legal_actions_not_iterating(self):
        assert_object_sets_equal(self.initial_state.legal_actions(self.role),
                                 self.legal_actions)

    def test_state_terms_iterating(self):
        assert_object_sets_equal(
            self.initial_state.state_propositions(),
            [GameProposition(prop) for prop in '1'])

    def test_state_terms_not_iterating(self):
        assert_object_sets_equal(
            list(self.initial_state.state_propositions()),
            [GameProposition(prop) for prop in '1'])

    def test_is_terminal(self):
        assert_false(self.initial_state.is_terminal())

    def test_game_id(self):
        assert_equal(str(self.initial_state.game_id()), 'buttonsandlights')

    def test_apply_moves_once(self):
        action = Action('a')
        new_state = self.initial_state.apply_moves({self.role: action})

        assert_equal(new_state.turn_number(), 1)
        assert_equal(new_state.utility(self.role), 0)
        assert_object_sets_equal(new_state.legal_actions(self.role),
                                 self.legal_actions)
        assert_object_sets_equal(new_state.state_propositions(),
                                 [GameProposition(prop) for prop in '2p'])
        assert_false(new_state.is_terminal())

    def test_apply_moves_check_initial(self):
        action = Action('a')
        self.initial_state.apply_moves({self.role: action})

        # Check that the initial state is unchanged
        assert_equal(self.initial_state.turn_number(), 0)
        assert_equal(self.initial_state.utility(self.role), 0)
        assert_object_sets_equal(self.initial_state.legal_actions(self.role),
                                 self.legal_actions)
        assert_object_sets_equal(self.initial_state.state_propositions(),
                                 [GameProposition(prop) for prop in '1'])
        assert_false(self.initial_state.is_terminal())

    def test_apply_moves_full_game_won(self):
        a = Action('a')
        b = Action('b')
        c = Action('c')
        final_state = self.initial_state.apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: c}).apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: a})

        assert_equal(final_state.turn_number(), 6)
        assert_equal(final_state.utility(self.role), 100)
        assert_object_sets_equal(final_state.legal_actions(self.role),
                                 self.legal_actions)
        assert_object_sets_equal(final_state.state_propositions(),
                                 [GameProposition(prop) for prop in '7pqr'])
        assert_true(final_state.is_terminal())

    def test_apply_moves_full_game_lost(self):
        a = Action('a')
        b = Action('b')
        c = Action('c')
        final_state = self.initial_state.apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: c}).apply_moves(
            {self.role: a}).apply_moves(
            {self.role: b}).apply_moves(
            {self.role: b})

        assert_equal(final_state.turn_number(), 6)
        assert_equal(final_state.utility(self.role), 0)
        assert_object_sets_equal(final_state.legal_actions(self.role),
                                 self.legal_actions)
        assert_object_sets_equal(final_state.state_propositions(),
                                 [GameProposition(prop) for prop in '7pr'])
        assert_true(final_state.is_terminal())


def test_play_tic_tac_toe():
    ggm = make_game_manager('tictactoe', TIC_TAC_TOE_FILE)
    game = ggm.game('tictactoe')
    state0 = game.initial_state()

    black = Role('black')
    white = Role('white')
    actions = {i: {j: Action("(mark {} {})".format(i, j))
                   for j in range(1, 4)}
               for i in range(1, 4)}

    all_actions = list(itertools.chain(*(
        value.values() for value in actions.values())))
    assert_object_sets_equal(game.all_actions(white), all_actions)
    assert_object_sets_equal(game.all_actions(black), all_actions)

    assert_equal(state0.turn_number(), 0)
    assert_equal(state0.utility(white), 50)
    assert_equal(state0.utility(black), 50)
    assert_false(state0.is_terminal())
    assert_object_sets_equal(
        state0.state_propositions(),
        [GameProposition('(cell {} {} b)'.format(i, j))
         for i in range(1, 4) for j in range(1, 4)] +
        [GameProposition('(step 1)')])

    state1 = state0.apply_moves({black: actions[2][2], white: actions[2][3]})
    state2 = state1.apply_moves({black: actions[1][2], white: actions[1][3]})
    state3 = state2.apply_moves({black: actions[2][1], white: actions[3][1]})

    assert_equal(state3.turn_number(), 3)
    assert_equal(state3.utility(white), 50)
    assert_equal(state3.utility(black), 50)
    assert_false(state3.is_terminal())
    assert_object_sets_equal(
        state3.legal_actions(white),
        [GameProposition('(mark {} {})'.format(i, j))
         for i, j in [(1, 1), (3, 2), (3, 3)]])

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

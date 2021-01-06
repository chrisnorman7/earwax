"""Test the ActionMap class."""

from earwax import Action, ActionMap


def test_init(action_map: ActionMap) -> None:
    """Test initialisation."""
    assert isinstance(action_map, ActionMap)
    assert action_map.actions == []


def test_action(action_map: ActionMap) -> None:
    """Test the action method."""

    @action_map.action('First action')
    def a() -> None:
        print('Works.')

    assert isinstance(a, Action)
    assert action_map.actions == [a]
    assert a.title == 'First action'
    assert a.symbol is None
    assert a.modifiers == 0
    assert a.hat_direction is None
    assert a.joystick_button is None
    assert a.mouse_button is None

    b: Action = action_map.action(
        'Second action', symbol=1, modifiers=2, joystick_button=3,
        mouse_button=4, hat_direction=(1, -1)
    )(print)

    assert isinstance(b, Action)
    assert action_map.actions == [a, b]
    assert b.title == 'Second action'
    assert b.func is print
    assert b.symbol == 1
    assert b.modifiers == 2
    assert b.joystick_button == 3
    assert b.mouse_button == 4
    assert b.hat_direction == (1, -1)


def test_add_actions(action_map: ActionMap) -> None:
    """Test the add_actions method."""
    am: ActionMap = ActionMap()

    @action_map.action('First Action')
    def a() -> None:
        pass

    @action_map.action('Second action')
    def b() -> None:
        pass

    am.add_actions(action_map)
    assert am.actions == action_map.actions
    am.actions.clear()

    @am.action('Third action')
    def c() -> None:
        pass
    am.add_actions(action_map)
    assert am.actions == [c, a, b]

"""Provides the ActionMap class."""

from typing import Callable, Optional

from attr import Factory, attrib, attrs

from .action import Action
from .types import ActionFunctionType, ActionListType, HatDirection


@attrs(auto_attribs=True)
class ActionMap:
    """An object to hold actions.

    This class is the answer to the question "What do I do when I have actions
    I want to be attached to multiple levels?"

    You could of course use a for loop, but this class is quicker::

        action_map: ActionMap = ActionMap()

        @action_map.action(...)

        @action_map.action(...)

        level: Level = Level(game)
        level.add_actions(action_map)

    :ivar ~earwax.ActionMap.actions: The actions to be stored on this map.
    """

    actions: 'ActionListType' = attrib(
        default=Factory(list), init=False, repr=False
    )

    def action(
        self, title: str, symbol: Optional[int] = None,
        mouse_button: Optional[int] = None, modifiers: int = 0,
        joystick_button: Optional[int] = None,
        hat_direction: Optional[HatDirection] = None,
        interval: Optional[float] = None
    ) -> Callable[[ActionFunctionType], Action]:
        """Add an action to this object.

        For example::

            @action_map.action(
                'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT,
                interval=0.5
            )
            def walk_forwards():
                # ...

        :param title: The :attr:`~earwax.Action.title` of the new action.

            This value is currently only used by :class:`earwax.ActionMenu`.

        :param symbol: The resulting action's :attr:`~earwax.Action.symbol`
            attribute.

        :param mouse_button: The resulting action's
            :attr:`~earwax.Action.mouse_button` attribute.

        :param modifiers: The resulting action's
            :attr:`~earwax.Action.modifiers` attribute.

        :param joystick_button: The resulting action's
            :attr:`~earwax.Action.joystick_button` attribute.

        :param hat_direction: The resulting action's
            :attr:`~earwax.Action.hat_direction` attribute.

        :param interval: The resulting action's :attr:`~earwax.Action.interval`
            attribute.
        """

        def inner(func: ActionFunctionType) -> Action:
            """Actually add the action."""
            a: Action = Action(
                title, func, symbol=symbol, mouse_button=mouse_button,
                modifiers=modifiers, joystick_button=joystick_button,
                hat_direction=hat_direction, interval=interval
            )
            self.actions.append(a)
            return a

        return inner

    def add_actions(self, action_map: 'ActionMap') -> None:
        """Add the actions from the provided map to this map.

        :param action_map: The map whose actions should be appended to this
            one.
        """
        self.actions.extend(action_map.actions)

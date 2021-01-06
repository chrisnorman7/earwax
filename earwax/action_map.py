"""Provides the ActionMap class."""

from typing import Callable

from attr import Factory, attrib, attrs

from .action import Action
from .types import ActionFunctionType, ActionListType


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

    def action(self, name: str, **kwargs) -> Callable[
        [ActionFunctionType], Action
    ]:
        """Add an action to this level.

        For example::

            @level.action(
                'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT,
                interval=0.5
            )
            def walk_forwards():
                # ...

        :param name: The name of the new action.

            The name is currently only used by :class:`earwax.ActionMenu`.

        :param kwargs: Extra keyword arguments to passed along to the
            constructor of :class:`earwax.Action`.
        """

        def inner(func: ActionFunctionType) -> Action:
            """Actually add the action."""
            a: Action = Action(name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

    def add_actions(self, action_map: 'ActionMap') -> None:
        """Add the actions from the provided map to this map.

        :param action_map: The map whose actions should be appended to this
            one.
        """
        self.actions.extend(action_map.actions)

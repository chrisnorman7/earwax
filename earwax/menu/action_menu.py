"""Provides the ActionMenu class."""

from inspect import isgenerator
from typing import Iterator, cast

from attr import attrs

from ..action import Action, ActionFunctionType, OptionalGenerator
from .menu import Menu


@attrs(auto_attribs=True)
class ActionMenu(Menu):
    """A menu to show a list of actions, and their associated triggers."""

    def __attrs_post_init__(self) -> None:
        """Add every action as an item."""
        super().__attrs_post_init__()
        if self.game.level is not None:
            a: Action
            for a in self.game.level.actions:
                self.add_item(str(a), self.handle_action(a))

    def handle_action(self, action: Action) -> ActionFunctionType:
        """Handle an action."""

        def inner() -> OptionalGenerator:
            """Pop the menu, and run the action."""
            yield
            self.game.pop_level()
            res = action.run(None)
            if isgenerator(res):
                next(cast(Iterator[None], res))
            return res

        return inner

"""Provides the ActionMenu class."""

from ..action import Action, ActionFunctionType, OptionalGenerator
from .menu import Menu


class ActionMenu(Menu):
    """A menu to show a list of actions, and their associated triggers."""

    def __attrs_post_init__(self) -> None:
        """Add every action as an item."""
        if self.game.level is not None:
            a: Action
            for a in self.game.level.actions:
                self.add_item(str(a), self.handle_action(a))

    def handle_action(self, action: Action) -> ActionFunctionType:
        """Handle an action."""

        def inner() -> OptionalGenerator:
            """Pop the menu, and run the action."""
            self.game.pop_level()
            return action.run(None)

        return inner

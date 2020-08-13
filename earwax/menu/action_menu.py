"""Provides the ActionMenu class."""

from inspect import isgenerator
from typing import Iterator, cast

from attr import attrs
from pyglet.window import key, mouse

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
                self.add_item(a.title, self.action_menu(a))

    def action_menu(self, action: Action) -> ActionFunctionType:
        """Show a menu of triggers for the given action."""

        def inner() -> None:
            func: ActionFunctionType = self.handle_action(action)
            m: Menu = Menu('Triggers', self.game)
            s: str
            mods: str = ''
            if action.modifiers:
                mods = key.modifiers_string(action.modifiers)
            if action.symbol is not None:
                s = key.symbol_string(action.symbol)
                if mods:
                    s = f'{mods} + {s}'
                m.add_item('Keyboard: ' + s, func)
            if action.mouse_button is not None:
                s = mouse.buttons_string(action.mouse_button)
                if mods:
                    s = f'{mods} + {s}'
                m.add_item('Mouse: ' + s, func)
            self.game.push_level(m)

        return inner

    def handle_action(self, action: Action) -> ActionFunctionType:
        """Handle an action."""

        def inner() -> OptionalGenerator:
            """Pop the menu, and run the action."""
            self.game.pop_level()
            self.game.pop_level()
            yield
            res = action.run(None)
            if isgenerator(res):
                next(cast(Iterator[None], res))
                try:
                    next(cast(Iterator[None], res))
                except StopIteration:
                    pass  # It's done.
            return res

        return inner

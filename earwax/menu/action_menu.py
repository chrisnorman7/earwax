"""Provides the ActionMenu class."""

from inspect import isgenerator
from typing import Iterator, cast

from attr import attrs
from pyglet.window import key, mouse

from ..action import Action, ActionFunctionType, OptionalGenerator
from .menu import Menu


@attrs(auto_attribs=True)
class ActionMenu(Menu):
    """A menu to show a list of actions, and their associated triggers.

    You can use this class with any game, like so:

    >>> from earwax import Game, Level, ActionMenu
    >>> from pyglet.window import Window, key
    >>> w = Window(caption='Test Game')
    >>> g = Game()
    >>> l = Level()
    >>> @l.action('Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
    ... def actions_menu():
    ...     '''Show an actions menu.'''
    ...     a = ActionMenu('Actions', g)
    ...     g.push_level(a)
    ...
    >>> g.push_level(l)
    >>> g.run(w)

    Now, if you press shift and slash (a question mark on english keyboards),
    you will get an action menu.

    If you want to override how triggers appear in the menu, then you can
    override :meth:`~ActionMenu.symbol_to_string` and
    :meth:`~ActionMenu.mouse_to_string`.
    """

    def __attrs_post_init__(self) -> None:
        """Add every action as an item."""
        super().__attrs_post_init__()
        if self.game.level is not None:
            a: Action
            for a in self.game.level.actions:
                self.add_item(a.title, self.action_menu(a))

    def symbol_to_string(self, action: Action) -> str:
        """Returns a string representing the symbol and modifiers needed to
        trigger the provided action.

        You can be certain that `action.symbol is not None`.

        Override this method to change how symbol triggers appear."""
        s: str
        mods: str = ''
        if action.modifiers:
            mods = key.modifiers_string(action.modifiers)
        s = key.symbol_string(action.symbol)
        if mods:
            s = f'{mods} + {s}'
        return s

    def mouse_to_string(self, action: Action) -> str:
        """Returns a string representing the mouse button and modifiers needed
        to trigger the provided action.

        You can be certain that `action.mouse_button is not None`.

        Override this method to change how mouse triggers appear."""
        s: str
        mods: str = ''
        if action.modifiers:
            mods = key.modifiers_string(action.modifiers)
        s = mouse.buttons_string(action.mouse_button)
        if mods:
            s = f'{mods} + {s}'
        return s

    def action_menu(self, action: Action) -> ActionFunctionType:
        """Show a submenu of triggers for the given action.

        Override this method to change how the submenu for actions are
        displayed."""

        def inner() -> None:
            func: ActionFunctionType = self.handle_action(action)
            m: Menu = Menu('Triggers', self.game)
            s: str
            if action.symbol is not None:
                s = self.symbol_to_string(action)
                m.add_item('Keyboard: ' + s, func)
            if action.mouse_button is not None:
                s = self.mouse_to_string(action)
                m.add_item('Mouse: ' + s, func)
            self.game.push_level(m)

        return inner

    def handle_action(self, action: Action) -> ActionFunctionType:
        """Handle an action.

        This method is used as the menu handler that is triggered when you
        select a trigger to activate the current action."""

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

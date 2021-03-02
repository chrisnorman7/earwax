"""Provides the ActionMenu class."""

from typing import List, Optional, Tuple

from attr import attrib, attrs
from pyglet.window import key, mouse

from ..action import Action
from ..hat_directions import DEFAULT, DOWN, LEFT, RIGHT, UP
from ..input_modes import InputModes
from ..types import ActionFunctionType, OptionalGenerator
from ..utils import english_list
from .menu import Menu


@attrs(auto_attribs=True)
class ActionMenu(Menu):
    """A menu to show a list of actions and their associated triggers.

    You can use this class with any game, like so::

        from earwax import Game, Level, ActionMenu
        from pyglet.window import Window, key
        w = Window(caption='Test Game')
        g = Game()
        l = Level()
        @l.action('Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
        def actions_menu():
            '''Show an actions menu.'''
            a = ActionMenu(g, 'Actions')
            g.push_level(a)

        g.push_level(l)
        g.run(w)

    Now, if you press shift and slash (a question mark on english keyboards),
    you will get an action menu.

    This code can be shortened to::

        @l.action('Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
        def actions_menu():
            '''Show an actions menu.'''
            game.push_action_menu()

    If you want to override how triggers appear in the menu, then you can
    override :meth:`~ActionMenu.symbol_to_string` and
    :meth:`~ActionMenu.mouse_to_string`.

    :ivar ~earwax.ActionMenu.input_mode: The input mode this menu will show
        actions for.

    :ivar ~earwax.ActionMenu.all_triggers_label: The label for the "All
        triggers" entry.

        If this value is ``None`` no such entry will be shown.
    """

    input_mode: Optional[InputModes] = attrib(repr=False)

    @input_mode.default
    def get_default_input_mode(instance: "ActionMenu") -> InputModes:
        """Get the default input mode."""
        return instance.game.input_mode

    all_triggers_label: Optional[str] = "<< Show all triggers >>"

    def __attrs_post_init__(self) -> None:
        """Add every action as an item."""
        super().__attrs_post_init__()
        if self.game.level is None:
            return  # Nothing to do.
        a: Action
        for a in self.game.level.actions:
            if self.input_mode is None:
                self.add_item(self.action_menu(a), title=a.title)
            else:
                func: ActionFunctionType = self.handle_action(a)
                triggers: List[str] = []
                if self.input_mode is InputModes.keyboard:
                    if a.symbol is not None:
                        triggers.append(self.symbol_to_string(a))
                    if a.mouse_button is not None:
                        triggers.append(
                            f"{self.mouse_to_string(a)} mouse button"
                        )
                elif self.input_mode is InputModes.controller:
                    if a.joystick_button is not None:
                        triggers.append(f"Button {a.joystick_button}")
                    if a.hat_direction is not None:
                        triggers.append(
                            f"{self.hat_direction_to_string(a.hat_direction)} "
                            "hat"
                        )
                else:
                    raise RuntimeError(
                        f"Invalid input mode: {self.input_mode!r}."
                    )
                self.add_item(func, title=self.action_title(a, triggers))
        if self.input_mode is not None and self.all_triggers_label is not None:
            self.add_item(self.show_all, title=self.all_triggers_label)

    def symbol_to_string(self, action: Action) -> str:
        """Describe how to trigger the given action with the keyboard.

        Returns a string representing the symbol and modifiers needed to
        trigger the provided action.

        You must be certain that ``action.symbol is not None``.

        Override this method to change how symbol triggers appear.

        :param action: The action whose :attr:`~earwax.Action.symbol` attribute
            this method will be working on.
        """
        s: str
        mods: str = ""
        if action.modifiers:
            mods = key.modifiers_string(action.modifiers)
        s = key.symbol_string(action.symbol)
        if mods:
            s = f"{mods} + {s}"
        return s

    def mouse_to_string(self, action: Action) -> str:
        """Describe how to trigger the given action with the mouse.

        Returns a string representing the mouse button and modifiers needed
        to trigger the provided action.

        You must be certain that ``action.mouse_button is not None``.

        Override this method to change how mouse triggers appear.

        :param action: The action whose :attr:`~earwax.Action.mouse_button`
            attribute this method will be working on.
        """
        s: str
        mods: str = ""
        if action.modifiers:
            mods = key.modifiers_string(action.modifiers)
        s = mouse.buttons_string(action.mouse_button)
        if mods:
            s = f"{mods} + {s}"
        return s

    def hat_direction_to_string(self, direction: Tuple[int, int]) -> str:
        """Return the given hat direction as a string."""
        if direction == DEFAULT:
            return "Default"
        elif direction == UP:
            return "Up"
        elif direction == DOWN:
            return "Down"
        elif direction == LEFT:
            return "Left"
        elif direction == RIGHT:
            return "Right"
        else:
            return str(direction)

    def action_menu(self, action: Action) -> ActionFunctionType:
        """Show a submenu of triggers.

        Override this method to change how the submenu for actions is
        displayed.

        :param action: The action to generate the menu for.
        """

        def inner() -> None:
            func: ActionFunctionType = self.handle_action(action)
            m: Menu = Menu(self.game, "Triggers")
            s: str
            if action.symbol is not None:
                s = self.symbol_to_string(action)
                m.add_item(func, title="Keyboard: " + s)
            if action.mouse_button is not None:
                s = self.mouse_to_string(action)
                m.add_item(func, title="Mouse: " + s)
            if action.joystick_button is not None:
                m.add_item(
                    func, title=f"Joystick: Button {action.joystick_button}"
                )
            if action.hat_direction is not None:
                d: str = self.hat_direction_to_string(action.hat_direction)
                m.add_item(func, title=f"Joystick: {d} hat")
            self.game.push_level(m)

        return inner

    def handle_action(self, action: Action) -> ActionFunctionType:
        """Handle an action.

        This method is used as the menu handler that is triggered when you
        select a trigger to activate the current action.

        :param action: The action to run.
        """

        def inner() -> OptionalGenerator:
            """Pop the menu, and run the action."""
            # First reveal this menu, as this method may be called from a sub
            # menu.
            self.game.reveal_level(self)
            # Now pop this menu off the stack.
            self.game.pop_level()
            return action.run(None)

        return inner

    def action_title(self, action: Action, triggers: List[str]) -> str:
        """Return a suitable title for the given action.

        This method is used when building the menu when
        :attr:`~earwax.ActionMenu.input_mode` is not ``None``.

        :param action: The action whose name will be used.

        :param triggers: A list of triggers gleaned from the given action.
        """
        triggers_str: str = english_list(
            triggers, empty="No triggers", and_="or "
        )
        return f"{action.title}: {triggers_str}"

    def show_all(self) -> None:
        """Show all triggers."""
        # First pop the level, so the right actions are processed.
        self.game.pop_level()
        m: ActionMenu = ActionMenu(
            self.game, self.title, input_mode=None  # type: ignore[arg-type]
        )
        self.game.push_level(m)

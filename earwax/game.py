"""Provides the Game class."""

from inspect import isgenerator

from attr import Factory, attrib, attrs
from pyglet import app, clock, options
from pyglet.window import Window, key

from earwax.speech import tts
from synthizer import initialized

from .action import Action, NoneType


@attrs
class Game:
    """The main game object.

    Although things like menus can be used without a Game object, this object
    is central to pretty much everything else."""

    # The title of the window that will be created.
    title = attrib()

    # A list of actions which can be called from within the game.
    actions = attrib(default=Factory(list), init=False)

    # The currently triggered actions.
    triggered_actions = attrib(default=Factory(list))

    # The actions which returned generators, and need to do something on key
    # release.
    on_key_release_generators = attrib(default=Factory(dict))

    # The window to display the game.
    window = attrib(default=Factory(NoneType), init=False)

    # The current menus (if any).
    menus = attrib(default=Factory(list), init=False)

    # The current editor.
    editor = attrib(default=Factory(NoneType))

    def start_action(self, a):
        """Start an action. If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to triggered_actions."""
        if a.interval is None:
            return a.run(None)
        else:
            self.triggered_actions.append(a)
            a.run(None)
            clock.schedule_interval(a.run, a.interval)

    def stop_action(self, a):
        """Unschedule an action, and remove it from triggered_actions."""
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol, modifiers):
        """A key has been pressed down."""
        for a in self.actions:
            if a.symbol == symbol and a.modifiers == modifiers:
                res = self.start_action(a)
                if isgenerator(res):
                    next(res)
                    self.on_key_release_generators[symbol] = res
        return True

    def on_key_release(self, symbol, modifiers):
        """A key has been released."""
        for a in self.triggered_actions:
            if a.symbol == symbol:
                self.stop_action(a)
        if symbol in self.on_key_release_generators:
            generator = self.on_key_release_generators.pop(symbol)
            try:
                next(generator)
            except StopIteration:
                pass

    def on_text(self, text):
        """Enter text into the current editor."""
        if self.editor is not None:
            return self.editor.on_text(text)

    def on_text_motion(self, motion):
        """Pass the motion onto any attached editor."""
        if self.editor is not None:
            return self.editor.on_text_motion(motion)

    def run(self):
        """Run the game."""
        options['shadow_window'] = False
        self.window = Window(caption=self.title)
        self.window.event(self.on_key_press)
        self.window.event(self.on_key_release)
        self.window.event(self.on_text)
        self.window.event(self.on_text_motion)
        with initialized():
            app.run()

    def action(self, name, **kwargs):
        """A decorator to add an action to this game."""

        def inner(func):
            """Actually add the action."""
            a = Action(self, name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

    def no_menu(self):
        """Returns True if there are no menus."""
        return len(self.menus) == 0

    def no_editor(self):
        """Returns true if there is no editor."""
        return self.editor is None

    def normal(self):
        """Returns True if both no_menu and no_editor are True."""
        return all([self.no_menu(), self.no_editor()])

    def push_menu(self, menu):
        """Push a menu onto self.menus."""
        self.menus.append(menu)
        menu.show_selection()

    def replace_menu(self, menu):
        """Pop the current menu, then push the new one."""
        self.pop_menu()
        self.push_menu(menu)

    def pop_menu(self):
        """Pop the most recent menu from the stack."""
        self.menus.pop()
        if not self.no_menu:
            self.menus[-1].show_selection()

    def clear_menus(self):
        """Pop all menus."""
        self.menus.clear()

    @property
    def menu(self):
        """Get the most recently added menu."""
        if len(self.menus):
            return self.menus[-1]

    def menu_activate(self):
        """Activate a menu item."""
        self.menu.activate()

    def dismiss(self):
        """Dismiss the currently active menu."""
        if self.menu is not None and self.menu.dismissible:
            self.pop_menu()
        elif self.editor is not None and self.editor.dismissible:
            self.editor = None
        else:
            return
        tts.speak('Cancel.')

    def menu_up(self):
        """Move up in a menu."""
        self.menu.move_up()

    def menu_down(self):
        """Move down in a menu."""
        self.menu.move_down()

    def submit_text(self):
        """Submit the text in an editor."""
        self.editor.submit()

    def add_default_actions(self):
        """Add actions relating to menus."""
        self.actions.extend(
            [
                Action(
                    self, 'Activate menu item', self.menu_activate,
                    symbol=key.RETURN, can_run=lambda: not self.no_menu() and
                    self.menu.position != -1
                ),
                Action(
                    self, 'Exit from a menu or editor', self.dismiss,
                    symbol=key.ESCAPE, can_run=lambda: True
                ),
                Action(
                    self, 'Move up in a menu', self.menu_up, symbol=key.UP,
                    can_run=lambda: not self.no_menu()
                ),
                Action(
                    self, 'Move down in a menu', self.menu_down,
                    symbol=key.DOWN, can_run=lambda: not self.no_menu()
                ),
                Action(
                    self, 'Submit text', self.submit_text, symbol=key.RETURN,
                    can_run=lambda: not self.no_editor()
                )
            ]
        )

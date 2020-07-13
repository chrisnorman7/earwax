"""Provides the Game class."""

from attr import Factory, attrib, attrs
from pyglet import app, clock, options
from pyglet.window import Window

from .action import Action


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

    # The window to display the game.
    window = attrib(default=Factory(type(None)), init=False)

    def on_key_press(self, symbol, modifiers):
        """A key has been pressed down."""
        for a in self.actions:
            if a.symbol == symbol and a.modifiers == modifiers:
                if a.interval is None:
                    a.func()
                else:
                    self.triggered_actions.append(a)
                    a.run(None)
                    clock.schedule_interval(a.run, a.interval)
        return True

    def on_key_release(self, symbol, modifiers):
        """A key has been released."""
        for a in self.triggered_actions:
            if a.symbol == symbol:
                self.triggered_actions.remove(a)
                clock.unschedule(a.run)

    def run(self):
        """Run the game."""
        options['shadow_window'] = False
        self.window = Window(caption=self.title)
        self.window.event(self.on_key_press)
        self.window.event(self.on_key_release)
        app.run()

    def action(self, name, **kwargs):
        """A decorator to add an action to this game."""
        kwargs['game'] = self

        def inner(func):
            """Actually add the action."""
            a = Action(name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

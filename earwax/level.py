"""Provides classes for working with levels."""

from inspect import isgenerator
from typing import (TYPE_CHECKING, Callable, Dict, Generator, Iterator, List,
                    cast)

from attr import Factory, attrib, attrs
from pyglet import clock

from .action import Action, ActionFunctionType, OptionalGenerator

if TYPE_CHECKING:
    from .game import Game

from .speech import tts

ActionListType = List[Action]
ReleaseGeneratorListType = Dict[int, Generator[None, None, None]]

MotionFunctionType = Callable[[], None]
MotionsType = Dict[int, MotionFunctionType]


@attrs(auto_attribs=True)
class Level:
    """A thing that contains event handlers. Can be pushed and pulled from
    within a Game instance."""

    # A list of actions which can be called on this object.
    actions: ActionListType = attrib(default=Factory(list), init=False)

    # The defined motion events. To define more, use the motion decorator.
    motions: MotionsType = attrib(Factory(dict), init=False)

    # The currently triggered actions.
    triggered_actions: 'ActionListType' = attrib(
        default=Factory(list), init=False
    )

    # The actions which returned generators, and need to do something on key
    # release.
    on_key_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )

    def start_action(self, a: Action) -> OptionalGenerator:
        """Start an action. If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to triggered_actions."""
        if a.interval is None:
            return a.run(None)
        else:
            self.triggered_actions.append(a)
            a.run(None)
            clock.schedule_interval(a.run, a.interval)
            return None

    def stop_action(self, a: Action) -> None:
        """Unschedule an action, and remove it from triggered_actions."""
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """A key has been pressed down."""
        a: Action
        for a in self.actions:
            if a.symbol == symbol and a.modifiers == modifiers:
                res: OptionalGenerator = self.start_action(a)
                if isgenerator(res):
                    next(cast(Iterator[None], res))
                    self.on_key_release_generators[symbol] = cast(
                        Generator[None, None, None], res
                    )
        return True

    def on_key_release(self, symbol: int, modifiers: int) -> bool:
        """A key has been released."""
        a: Action
        for a in self.triggered_actions:
            if a.symbol == symbol:
                self.stop_action(a)
        if symbol in self.on_key_release_generators:
            generator: Generator[
                None, None, None
            ] = self.on_key_release_generators.pop(symbol)
            try:
                next(generator)
            except StopIteration:
                pass
        return True

    def on_text(self, text: str) -> bool:
        """Enter text into the current editor."""
        return True

    def on_text_motion(self, motion: int) -> bool:
        """Handle a motion event."""
        if motion in self.motions:
            self.motions[motion]()
            return True
        return False

    def action(self, name: str, **kwargs) -> Callable[
        [ActionFunctionType], Action
    ]:
        """A decorator to add an action to this level."""

        def inner(func: ActionFunctionType) -> Action:
            """Actually add the action."""
            a: Action = Action(self, name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

    def motion(self, motion: int) -> Callable[
        [MotionFunctionType], MotionFunctionType
    ]:
        """A decorator to add a handler to self.motions."""

        def inner(func: MotionFunctionType) -> MotionFunctionType:
            self.motions[motion] = func
            return func

        return inner

    def on_push(self) -> None:
        """This level has been pushed onto the level stack of the game."""
        pass

    def on_pop(self) -> None:
        """This level has been popped from the stack."""
    pass

    def on_reveal(self) -> None:
        """A level which had been previously pushed over this one has now been
        popped, revealing this one."""
        pass


@attrs(auto_attribs=True)
class GameMixin:
    """Add a game attribute to any level."""

    # The game this level is bound to.
    game: 'Game'


@attrs(auto_attribs=True)
class DismissibleMixin(GameMixin):
    """Make something dismissible."""

    # Whether or not it should be possible to dismiss this level.
    dismissible: bool = Factory(lambda: True)

    def dismiss(self) -> None:
        """Dismiss the currently active menu."""
        if self.dismissible:
            self.game.pop_level()
            tts.speak('Cancel.')


@attrs(auto_attribs=True)
class TitleMixin:
    "Add a title to any level."""

    # The title of this menu.
    title: str

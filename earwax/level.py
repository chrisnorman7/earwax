"""Provides classes for working with levels."""

from typing import TYPE_CHECKING, Callable

from attr import Factory, attrib, attrs

from .action import Action, ActionFunctionType

if TYPE_CHECKING:
    from .game import Game, ActionListType, MotionsType, MotionFunctionType

from .speech import tts


@attrs(auto_attribs=True)
class Level:
    """A thing that contains event handlers. Can be pushed and pulled from
    within a Game instance."""

    # A list of actions which can be called on this object.
    actions: 'ActionListType' = attrib(default=Factory(list), init=False)

    # The defined motion events. To define more, use the motion decorator.
    motions: 'MotionsType' = attrib(Factory(dict), init=False)

    def on_text(self, text: str) -> bool:
        """Enter text into the current editor."""
        return True

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
        ['MotionFunctionType'], 'MotionFunctionType'
    ]:
        """A decorator to add a handler to self.motions."""

        def inner(func: 'MotionFunctionType') -> 'MotionFunctionType':
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

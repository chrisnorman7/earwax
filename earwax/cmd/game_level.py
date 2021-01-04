"""Provides the GameLevel class."""

from typing import List, Optional, Union

from attr import Factory, attrs
from shortuuid import uuid

from ..mixins import DumpLoadMixin


@attrs(auto_attribs=True)
class Trigger(DumpLoadMixin):
    """A trigger that can activate a function in a game."""

    symbol: Optional[str] = None
    modifiers: List[str] = Factory(list)
    mouse_button: Optional[str] = None
    hat_directions: Optional[str] = None
    joystick_button: Optional[int] = None


@attrs(auto_attribs=True)
class GameLevelScript(DumpLoadMixin):
    """A script which is attached to a game level."""

    name: str
    trigger: Trigger
    code: str
    id: str = Factory(uuid)


@attrs(auto_attribs=True)
class LevelData(DumpLoadMixin):
    """A standard earwax level.

    An instance of this class can be used to build a :class:`earwax.Level`
    instance.
    """


@attrs(auto_attribs=True)
class BoxLevelData(DumpLoadMixin):
    """A box level.

    An instance of this class can be used to build a :class:`earwax.BoxLevel`
    instance.
    """

    bearing: int = Factory(int)


@attrs(auto_attribs=True)
class GameLevel(DumpLoadMixin):
    """A game level.

    This class is used in the GUI so that non-programmers can can create levels
    with no code.

    :ivar ~earwax.cmd.game_level.GameLevel.name: The name of this level.

    :ivar ~earwax.cmd.game_level.GameLevel.data: The data for this level.

    :ivar ~earwax.cmd.game_level.GameLevel.scripts: The scripts that are
        attached to this level.
    """

    name: str
    data: Union[LevelData, BoxLevelData]
    scripts: List[GameLevelScript] = Factory(list)
    id: str = Factory(uuid)

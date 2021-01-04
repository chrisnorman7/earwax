"""Provides the GameLevel class."""

from pathlib import Path
from typing import List, Optional, Union

from attr import Factory, attrs
from shortuuid import uuid

from ..mixins import DumpLoadMixin
from .constants import scripts_directory


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
    id: str = Factory(uuid)

    @property
    def script_name(self) -> str:
        """Return the script name (although not the path) for this script.

        If you want the path, use the :attr:`~script_path` attribute.
        """
        name: str = f'script_{self.id}'
        assert name.isidentifier(), f'{name} is not a valid identifier.'
        return name + '.py'

    @property
    def script_path(self) -> Path:
        """Return the path where code for this script resides.

        If you want the filename, use the :attr:`~script_name` attribute.
        """
        return scripts_directory / self.script_name

    @property
    def code(self) -> str:
        """Return the code of this script.

        If :attr:`~script_path` does not exist, an empty string will be
        returned.
        """
        if not self.script_path.is_file():
            return ''
        with self.script_path.open('r') as f:
            return f.read()

    @code.setter
    def code(self, code: str) -> None:
        """Set the code."""
        with self.script_path.open('w') as f:
            f.write(code)


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

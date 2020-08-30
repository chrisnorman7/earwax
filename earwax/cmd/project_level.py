"""Provides the GameLevel class."""

from pathlib import Path
from typing import Any, Dict, List

from attr import Attribute, Factory, asdict, attrib, attrs
from shortuuid import uuid
from yaml import dump

from ..level import GameMixin, Level, TitleMixin
from .constants import levels_directory

DumpDict = Dict[str, Any]


@attrs(auto_attribs=True)
class ProjectLevel(TitleMixin, GameMixin, Level):
    """A level in an Earwax project.

    This class attempts to be as neutral as possible, so you can build your own
    systems on top of it by subclassing.

    That said, it does provide some defaults that should be useful in a wide
    variety of situations.

    :ivar ~earwax.GameLevel.id: The unique ID of this level.

        By default, this is provided by the `shortuuid
        <https://pypi.org/project/shortuuid/>`__ package.

        Used by various build tools to reference other levels.

    :ivar ~earwax.GameLevel.min_x: The minimum x value.

    :ivar ~earwax.GameLevel.max_x: The maximum x value.

    :ivar ~earwax.GameLevel.min_y: The minimum y value.

    :ivar ~earwax.GameLevel.max_y: The maximum y value.

    :ivar ~earwax.GameLevel.undumped_attributes: A list of attributes which
        should be ignored by the :meth:`~earwax.GameLevel.dump` method.
    """

    id: str = Factory(uuid)
    min_x: int = 0
    max_x: int = 200
    min_y: int = 0
    max_y: int = 200

    undumped_attributes: List[str] = attrib(
        default=Factory(lambda: [
            'game', 'actions', 'motions', 'undumped_attributes'
        ]), init=False
    )

    def dump(self) -> DumpDict:
        """Return this object as a dictionary.

        Used for serialisation."""
        return asdict(self, filter=self.should_dump)

    def should_dump(self, a: Attribute, v: Any) -> bool:
        """Returns a boolean representing whether or not a particular attribute
        should be dumped.

        :param a: The ``attr.Attribute`` instance that is being tested.

        :param name: The value that will be returned.
        """
        return a.name not in self.undumped_attributes

    def save(self) -> None:
        """Save this level to ``levels_directory``."""
        p: Path = levels_directory / (self.id + '.yaml')
        with p.open('w') as f:
            dump(self.dump(), stream=f)

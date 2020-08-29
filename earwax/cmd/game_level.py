"""Provides the GameLevel class."""

from typing import Any, Dict, List

from attr import Attribute, Factory, attrib, attrs, asdict
from shortuuid import uuid

from earwax.level import GameMixin, Level, TitleMixin

DumpDict = Dict[str, Any]


@attrs(auto_attribs=True)
class GameLevel(TitleMixin, GameMixin, Level):
    """A map in a game."""

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

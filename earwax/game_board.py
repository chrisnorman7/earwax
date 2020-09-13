"""Provides the GameBoard class."""

from typing import Callable, Generic, List, Optional, TypeVar

from attr import Factory, attrib, attrs
from pyglet.event import EventDispatcher

from .level import Level
from .point import Point, PointDirections
from .walking_directions import walking_directions

T = TypeVar('T')


class NoSuchTile(Exception):
    """No such tile exists.

    This exception is raised by :meth:`earwax.GameBoard.get_tile` when no tile
    is found at the given coordinates.
    """


@attrs(auto_attribs=True)
class GameBoard(Level, EventDispatcher, Generic[T]):
    """A useful starting point for making board games.

    :ivar ~earwax.GameBoard.size: The size of this board.

        The passed value will be the maximum possible coordinates on the board,
        with ``(0, 0, 0)`` being the minimum.

    :ivar ~earwax.GameBoard.tile_builder: The function that is used to build
        the GameBoard.

        The return value of this function should be of type ``T``.

    :ivar ~earwax.GameBoard.coordinates: The coordinates of the player on this
        board.
    """

    size: Point
    tile_builder: Callable[[Point], T]

    coordinates: Point = Factory(lambda: Point(0, 0, 0))

    tiles: List[List[List[T]]] = attrib(default=Factory(list), init=False)

    def __attrs_post_init__(self) -> None:
        """Populate the board."""
        x: int = 0
        while x <= self.size.x:
            self.tiles.append([])
            y: int = 0
            while y <= self.size.y:
                self.tiles[x].append([])
                z: int = 0
                while z <= self.size.z:
                    self.tiles[x][y].append(self.tile_builder(Point(x, y, z)))
                    z += 1
                y += 1
            x += 1
        self.register_event_type('on_move')
        self.register_event_type('on_move_fail')

    def get_tile(self, p: Point) -> T:
        """Return the tile at the given point.

        If there is no tile found, then :class:`~earwax.NoSuchTile` is raised.

        :param p: The coordinates of the desired tile.
        """
        x: int
        y: int
        z: int
        x, y, z = p.floor().coordinates  # type: ignore[assignment]
        try:
            return self.tiles[x][y][z]
        except IndexError:
            raise NoSuchTile()

    @property
    def current_tile(self) -> Optional[T]:
        """Gets the tile at the current coordinates.

        If no such tile is found, ``None`` is returned.
        """
        try:
            return self.get_tile(self.coordinates)
        except NoSuchTile:
            return None

    def on_move(self, direction: PointDirections, tile: T) -> None:
        """An event that is dispatched by :meth:`~earwax.GameBoard.move`.

        :param direction: The direction the player just moved.
        """
        pass

    def on_move_fail(self, direction: PointDirections) -> None:
        """An event that is dispatched when a player fails to move in the given
        direction.

        :param direction: The direction the player tried to move in.
        """
        pass

    def move(
        self, direction: PointDirections, wrap: bool = False
    ) -> Callable[[], None]:
        """Returns a callable that can be used to move the player.

        For example::

            board = GameBoard(...)

            board.action(
                'Move left', symbol=key.LEFT
            )(board.move(PointDirections.west))

        :param direction: The direction that this action should move the player
            in.

        :param wrap: If ``True``, then coordinates that are out of range will
            result in wrapping around to the other side of the board..
        """

        def inner() -> None:
            p = self.coordinates + walking_directions[direction]
            try:
                name: str
                value: float
                size_value: float
                for name in ('x', 'y', 'z'):
                    value = getattr(p, name)
                    size_value = getattr(self.size, name)
                    if value < 0:
                        if not wrap:
                            raise NoSuchTile()
                        setattr(p, name, value + size_value)
                    elif value > size_value:
                        if not wrap:
                            raise NoSuchTile()
                        setattr(p, name, 0)
                tile: T = self.get_tile(p)
                self.coordinates = p
                self.dispatch_event('on_move', direction, tile)
            except NoSuchTile:
                self.dispatch_event('on_move_fail', direction)

        return inner
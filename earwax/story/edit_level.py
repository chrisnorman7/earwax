"""Provides the EditLevel class."""

from typing import Callable, List, Optional

from attr import attrs
from shortuuid import uuid

from ..game import Game
from ..menu import Menu
from .play_level import PlayLevel
from .world import WorldRoom

try:
    from pyglet.window import key
except ModuleNotFoundError:
    key = None


def push_rooms_menu(
    game: Game, rooms: List[WorldRoom], activate: Callable[[WorldRoom], None]
) -> None:
    """Push a menu with all the provided rooms.

    :param game: The game to pop this level from when a room is selected.

    :param rooms: The rooms which should show up in the menu.

    :param activate: The function to call with the selected room.
    """
    m: Menu = Menu(game, 'Select a room')
    room: WorldRoom
    for room in rooms:

        def inner(r: WorldRoom = room) -> None:
            """Pop the menu, and call ``activate(room)``."""
            game.pop_level()
            game.output(r.get_name())
            activate(r)

        m.add_item(inner, title=f'{room.get_name()}: {room.get_description()}')

    game.push_level(m)


@attrs(auto_attribs=True)
class EditLevel(PlayLevel):
    """A level for editing stories."""

    filename: Optional[str] = None

    def __attrs_post_init__(self) -> None:
        """Add some more actions."""
        self.action('Save world', symbol=key.S, modifiers=key.MOD_CTRL)(
            self.save
        )
        self.action('Go to another room', symbol=key.G)(self.goto_room)
        self.action('Create room', symbol=key.R)(self.create_room)
        return super().__attrs_post_init__()

    def save(self) -> None:
        """Save the world."""
        try:
            with open(self.filename, 'w') as f:
                f.write(self.world.to_string())
            self.game.output('Saved.')
        except Exception as e:
            self.game.output(str(e))
            raise

    def goto_room(self) -> None:
        """Let the player choose a room to go to."""
        push_rooms_menu(
            self.game, list(self.world.rooms.values()), self.set_room
        )

    def create_room(self) -> None:
        """Create a new room."""
        r: WorldRoom = WorldRoom(self.world, uuid())
        self.world.add_room(r)
        self.set_room(r)
        self.game.output(r.get_name())

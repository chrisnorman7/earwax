"""Provides the EditLevel class."""

from inspect import isgenerator
from typing import Callable, Generator, List, Optional, Union

from attr import attrs
from shortuuid import uuid

from ..editor import Editor
from ..game import Game
from ..menu import Menu
from ..types import OptionalGenerator
from .play_level import PlayLevel
from .world import ObjectTypes, RoomExit, RoomObject, WorldAction, WorldRoom

try:
    from pyglet.window import key
except ModuleNotFoundError:
    key = None


def push_rooms_menu(
    game: Game, rooms: List[WorldRoom],
    activate: Callable[[WorldRoom], OptionalGenerator]
) -> None:
    """Push a menu with all the provided rooms.

    :param game: The game to pop this level from when a room is selected.

    :param rooms: The rooms which should show up in the menu.

    :param activate: The function to call with the selected room.
    """
    m: Menu = Menu(game, 'Select a room')
    room: WorldRoom
    for room in rooms:

        def inner(r: WorldRoom = room) -> OptionalGenerator:
            """Pop the menu, and call ``activate(room)``."""
            game.pop_level()
            game.output(r.get_name())
            res: OptionalGenerator = activate(r)
            if res is not None and isgenerator(res):
                yield from res
            else:
                return res

        m.add_item(inner, title=f'{room.get_name()}: {room.get_description()}')

    game.push_level(m)


def push_actions_menu(
    game: Game, actions: List[WorldAction],
    activate: Callable[[WorldAction], OptionalGenerator]
) -> None:
    """Push a menu that lets the player select an action.

    :param game: The game to use when constructing the menu.

    :param actions: A list of actions to show.

    :param activate: A function to call with the chosen action.
    """
    m: Menu = Menu(game, 'Actions')
    a: WorldAction
    for a in actions:

        def inner(action: WorldAction = a) -> OptionalGenerator:
            """Pop the level and call ``activate``."""
            game.pop_level()
            res: OptionalGenerator = activate(action)
            if res is not None and isgenerator(res):
                yield from res
            else:
                return res

        m.add_item(inner, title=a.name)
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
        self.action('Create menu', symbol=key.C)(self.create_menu)
        self.action('Rename the currently focused object', symbol=key.R)(
            self.rename
        )
        self.action(
            'Shadow room name', symbol=key.R, modifiers=key.MOD_SHIFT
        )(self.shadow_name)
        self.action('Describe this room', symbol=key.D)(self.describe_room)
        self.action(
            'Shadow room description', symbol=key.D, modifiers=key.MOD_SHIFT
        )(self.shadow_description)
        self.action('Change message', symbol=key.M)(self.remessage)
        return super().__attrs_post_init__()

    @property
    def room(self) -> WorldRoom:
        """Return the current room."""
        return self.state.room

    @property
    def object(self) -> Optional[ObjectTypes]:
        """Return the object from ``self.state``."""
        return self.state.object

    def get_rooms(self, include_current: bool = True) -> List[WorldRoom]:
        """Return a list of rooms from this world.

        :param include_current: If this value is ``True``, the current room
            will be included.
        """
        rooms: List[WorldRoom] = list(self.world.rooms.values())
        if not include_current:
            rooms.remove(self.room)
        return rooms

    def save(self) -> None:
        """Save the world."""
        assert self.filename
        try:
            with open(self.filename, 'w') as f:
                f.write(self.world.to_string())
            self.game.output('Saved.')
        except Exception as e:
            self.game.output(str(e))
            raise

    def describe_room(self) -> Generator[None, None, None]:
        """Set the description for the current room."""
        r: WorldRoom = self.room
        e: Editor = Editor(self.game, text=r.description)

        @e.event
        def on_submit(text: str) -> None:
            """Set the description."""
            self.game.pop_level()
            r.description = text
            self.game.output('Description set.')

        self.game.output('Enter a new description: %s' % r.description)
        yield
        self.game.push_level(e)

    def rename(self) -> Generator[None, None, None]:
        """Rename the currently focused object."""
        obj: Optional[ObjectTypes] = self.object
        if obj is None:
            self.game.output('No object selected.')
        elif isinstance(obj, (WorldRoom, RoomObject)):
            yield from self.set_name(obj)
        else:
            assert isinstance(obj, RoomExit)
            yield from self.set_name(obj.action)

    def shadow_name(self) -> None:
        """Sow a menu to select another room whose name will be shadowed."""
        room: WorldRoom = self.room

        def inner(other: WorldRoom) -> None:
            """Set the room name."""
            room.name = f'#{other.id}'

        push_rooms_menu(
            self.game, self.get_rooms(include_current=False), inner
        )

    def shadow_description(self) -> None:
        """Set the description of this room from another room."""
        current_room: WorldRoom = self.room

        def inner(new_room: WorldRoom) -> None:
            """Set the description of this room."""
            current_room.description = f'#{new_room.id}'
            self.game.output('Description set.')

        push_rooms_menu(
            self.game, self.get_rooms(include_current=False), inner
        )

    def goto_room(self) -> None:
        """Let the player choose a room to go to."""
        push_rooms_menu(self.game, self.get_rooms(), self.set_room)

    def create_menu(self) -> None:
        """Show the creation menu."""
        m: Menu = Menu(self.game, title='Create')
        m.add_item(self.create_exit, title='Exit')
        m.add_item(self.create_object, title='Object')
        m.add_item(self.create_room, title='Room')
        self.game.push_level(m)

    def create_exit(self) -> None:
        """Link this room to another."""
        self.game.pop_level()
        room: WorldRoom = self.room

        def inner(destination: WorldRoom) -> None:
            """Create the exit."""
            x: RoomExit = RoomExit(room, destination.id)
            room.exits.append(x)
            self.game.output('Exit created.')

        push_rooms_menu(
            self.game, self.get_rooms(include_current=False), inner
        )

    def create_object(self) -> None:
        """Create a new object in the current room."""
        self.game.pop_level()
        room: WorldRoom = self.room
        obj: RoomObject = RoomObject(uuid(), room)
        room.objects[obj.id] = obj
        self.game.output('Object created.')

    def create_room(self) -> None:
        """Create a new room."""
        self.game.pop_level()
        r: WorldRoom = WorldRoom(self.world, uuid())
        self.world.add_room(r)
        self.set_room(r)
        self.game.output(r.get_name())

    def set_name(
        self, obj: Union[WorldAction, RoomObject, WorldRoom]
    ) -> Generator[None, None, None]:
        """Push an editor that can be used to change the name of ``obj``.

        :param obj: The object to rename.
        """
        e: Editor = Editor(self.game, text=obj.name)

        @e.event
        def on_submit(text: str) -> None:
            """Rename ``obj``."""
            obj.name = text
            self.game.pop_level()
            self.game.output('Done.')

        self.game.output('Enter a new name for %s:' % obj.name)
        yield
        self.game.push_level(e)

    def set_message(self, action: WorldAction) -> Generator[None, None, None]:
        """Push an editor to set the message on the provided action.

        :param action: The action whose message attribute will be modified.
        """
        print('Hello.')
        e: Editor = Editor(self.game, text=action.message or '')

        @e.event
        def on_submit(text: str) -> None:
            """Set the message."""
            action.message = text
            self.game.pop_level()
            self.game.output('Message set.')

        self.game.output(
            f'Enter a new message for {action.name}: {action.message}'
        )
        yield
        self.game.push_level(e)

    def remessage(self) -> OptionalGenerator:
        """Set a message on the currently-focused object."""
        obj: Optional[ObjectTypes] = self.object
        if obj is None:
            self.game.output('No object selected.')
        elif isinstance(obj, WorldRoom):
            return self.game.output('Rooms do not have messages.')
        elif isinstance(obj, RoomExit):
            yield from self.set_message(obj.action)
        else:
            push_actions_menu(self.game, obj.actions, self.set_message)

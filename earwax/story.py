"""Provides classes related to XML stories."""

from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Generator, List, Optional, Tuple, Union
from xml.etree.ElementTree import Element

from attr import Factory, attrib, attrs

from .menu import Menu
from .sound import SoundManager
from .track import Track, TrackTypes

try:
    from pyglet.window import key
    from synthizer import DirectSource, Source3D
except ModuleNotFoundError:
    key = None
    DirectSource, Source3D = (object, object)

from shortuuid import uuid
from xml_python import Builder, NoneType

from .level import Level


@attrs(auto_attribs=True)
class WorldSound:
    """A sound which is heard when something happens in the story."""

    path: Path


@attrs(auto_attribs=True)
class WorldAmbiance(WorldSound):
    """An ambiance."""

    position: Optional[Tuple[float, float, float]] = None


@attrs(auto_attribs=True)
class WorldAction:
    """An action that can be performed.

    This class is used on objects, and when walking through doors.
    """

    name: str = 'Unnamed Action'
    message: Optional[str] = None
    sound: Optional[WorldSound] = None


@attrs(auto_attribs=True)
class RoomObject:
    """An object in the story.

    Will either sit in a room, or be in the player's inventory.
    """

    id: str
    location: 'WorldRoom'
    position: Optional[Tuple[float, float, float]] = None
    name: str = 'Unnamed Object'
    ambiances: List[WorldAmbiance] = Factory(list)
    actions: List[WorldAction] = Factory(list)


@attrs(auto_attribs=True)
class RoomExit:
    """An exit between two rooms."""

    location: 'WorldRoom'
    destination_id: str
    action: WorldAction = Factory(WorldAction)

    @property
    def destination(self) -> 'WorldRoom':
        """Return the room this exit leads from."""
        return self.location.world.rooms[self.destination_id]


@attrs(auto_attribs=True)
class WorldRoom:
    """A room in a world."""

    world: 'StoryWorld'
    id: str
    name: str = 'Unnamed Room'
    description: str = 'Not described.'
    ambiances: List[WorldAmbiance] = Factory(list)
    objects: Dict[str, RoomObject] = Factory(dict)
    exits: List[RoomExit] = Factory(list)


@attrs(auto_attribs=True)
class WorldMessages:
    """All the messages that can be shown to the player."""

    no_objects: str = 'This room is empty.'
    no_actions: str = 'There is nothing you can do with this object.'
    actions_menu: str = 'You step up to {}.'
    no_exits: str = 'There is no way out of this room.'
    room_activate: str = 'You cannot do that.'
    room_category: str = 'Location'
    objects_category: str = 'Objects'
    exits_category: str = 'Exits'


@attrs(auto_attribs=True)
class StoryWorld:
    """The top level world object."""

    name: str = 'Untitled World'
    author: str = 'Unknown'

    rooms: Dict[str, WorldRoom] = Factory(dict)
    initial_room_id: Optional[str] = None
    messages: WorldMessages = Factory(WorldMessages)

    @property
    def initial_room(self) -> Optional[WorldRoom]:
        """Return the initial room for this world."""
        return self.rooms[self.initial_room_id]


class StoryStateCategories(Enum):
    """The story state categories."""

    room = 0
    objects = 1
    exits = 2


@attrs(auto_attribs=True)
class WorldState:
    """The state of a story."""

    world: StoryWorld

    room_id: Optional[str] = None
    inventory_ids: List[str] = Factory(list)
    category_index: int = Factory(int)
    object_index: Optional[int] = None

    @property
    def room(self) -> WorldRoom:
        """Get the current room."""
        return self.world.rooms[self.room_id]

    @property
    def category(self) -> StoryStateCategories:
        """Return the current category."""
        return list(StoryStateCategories)[self.category_index]


def set_name(
    thing: Union[StoryWorld, WorldRoom, WorldAction], element: Element
) -> None:
    """Set the world name."""
    name: Optional[str] = element.text
    if name is None:
        room_id: Optional[str] = element.attrib.get('id', None)
        if room_id is None:
            raise RuntimeError(
                'An empty name was given, with no room ID to copy the name '
                'from.'
            )
        elif not isinstance(thing, WorldRoom):
            raise RuntimeError(
                'Names can only be copied by rooms from other rooms.'
            )
        elif room_id not in thing.world.rooms:
            raise RuntimeError(
                'Invalid room ID %r. That room may not have been loaded yet.' %
                room_id
            )
        else:
            name = thing.world.rooms[room_id].name
    thing.name = name
    assert isinstance(thing.name, str)


def set_ambiance(
    parent: Union[WorldRoom, RoomObject], element: Element
) -> None:
    """Set the ambiance for a room."""
    if element.text is None:
        raise RuntimeError(
            'You must provide a path for the ambiance of %s.' % parent.name
        )
    p: Path = Path(element.text)
    if not p.exists():
        raise RuntimeError(
            'The ambiance for %s is invalid: %s.' % (parent.name, element.text)
        )
    a: WorldAmbiance = WorldAmbiance(element.text)
    if isinstance(parent, RoomObject):
        a.position = parent.position
    parent.ambiances.append(a)


def make_action(
    obj: Union[RoomExit, RoomObject], element: Element
) -> WorldAction:
    """Make a new action."""
    action: WorldAction = WorldAction()
    if isinstance(obj, RoomExit):
        obj.action = action
    elif isinstance(obj, RoomObject):
        obj.actions.append(action)
    else:
        raise RuntimeError('Invalid action placement: below object %r.' % obj)
    return action


action_builder: Builder[
    Union[RoomObject, RoomExit], WorldAction
] = Builder(
    make_action, name='Action', parsers={
        'name': set_name,
    }
)


@action_builder.parser('message')
def set_action_message(action: WorldAction, element: Element) -> None:
    """Set the action message."""
    action.message = element.text


@action_builder.parser('sound')
def set_sound(action: WorldAction, element: Element) -> None:
    """Set the action sound."""
    if element.text is None:
        raise RuntimeError('Empty sound tag for action %s.' % action.name)
    p: Path = Path(element.text)
    if not p.exists():
        raise RuntimeError(
            'Invalid sound for action %s: %r: Path does not exist.' % (
                action.name, element.text
            )
        )
    action.sound = p


def make_object(room: WorldRoom, element: Element) -> RoomObject:
    """Make a story object instance."""
    obj: RoomObject = RoomObject(element.attrib.get('str', uuid()), room)
    coordinates: List[float] = []
    name: str
    for name in ('x', 'y', 'z'):
        value: str = element.attrib.get(name, '0')
        try:
            coordinates.append(float(value))
        except ValueError:
            raise RuntimeError(
                'Invalid %s coordinate for object in room %s (#%s): %r.' % (
                    name, room.name, room.id, value
                )
            )
    if coordinates != [0.0, 0.0, 0.0]:
        obj.position = tuple(coordinates)
    room.objects[obj.id] = obj
    return obj


object_builder: Builder[WorldRoom, RoomObject] = Builder(
    make_object, name='Object', parsers={
        'name': set_name,
        'ambiance': set_ambiance
    }, builders={
        'action': action_builder
    }
)


def make_exit(room: WorldRoom, element: Element) -> RoomExit:
    """Make a room exit."""
    destination_id: Optional[str] = element.attrib.get('destination', None)
    if destination_id is None:
        raise RuntimeError(
            'Cannot make exit from room %s with no destination id.' % room.name
        )
    x: RoomExit = RoomExit(room, destination_id)
    room.exits.append(x)
    return x


exit_builder: Builder[WorldRoom, RoomExit] = Builder(
    make_exit, name='Exit', builders={
        'action': action_builder
    }
)


def make_room(world: StoryWorld, element: Element) -> WorldRoom:
    """Make a new room."""
    room: WorldRoom = WorldRoom(world, element.attrib.get('id', uuid()))
    world.rooms[room.id] = room
    return room


room_builder: Builder[StoryWorld, WorldRoom] = Builder(
    make_room, name='Room', parsers={
        'name': set_name,
        'ambiance': set_ambiance
    }, builders={
        'object': object_builder,
        'exit': exit_builder
    }
)


@room_builder.parser('description')
def set_description(room: WorldRoom, element: Element) -> None:
    """Set the description."""
    if element.text is not None:
        room.description = element.text
    else:
        room_id: Optional[str] = element.attrib.get('id', None)
        if room_id is None:
            raise RuntimeError(
                'An empty description was given, with no room ID to copy the '
                'description from.'
            )
        elif room_id not in room.world.rooms:
            raise RuntimeError(
                'Invalid room ID %r. That room may not have been loaded yet.' %
                room_id
            )
        else:
            room.description = room.world.rooms[room_id].description


def make_story(parent: NoneType, element: Element) -> StoryWorld:
    """Make a story object."""
    return StoryWorld()


story_builder: Builder[NoneType, StoryWorld] = Builder(
    make_story, name='Story', builders={'room': room_builder},
    parsers={'name': set_name}
)


@story_builder.parser('entrance')
def set_entrance(world: StoryWorld, element: Element) -> None:
    """Set the initial room."""
    world.initial_room_id = element.text


@story_builder.parser('author')
def set_author(world: StoryWorld, element: Element) -> None:
    """Set the author."""
    world.author = element.text


@story_builder.parser('message')
def set_world_message(world: StoryWorld, element: Element) -> None:
    """Set a message on the world."""
    message_ids: List[str] = list(world.messages.__annotations__)
    message_id: Optional[str] = element.attrib.get('id', None)
    if message_id is None:
        raise RuntimeError('All world messages must have IDs.')
    elif message_id not in message_ids:
        raise RuntimeError(
            'Invalid message ID %r. Valid IDs: %s' % (
                message_id, ', '.join(message_ids)
            )
        )
    elif element.text is None:
        raise RuntimeError('Tried to blank the %r message.' % message_id)
    else:
        setattr(world.messages, message_id, element.text)


@attrs(auto_attribs=True)
class StoryLevel(Level):
    """A level that can be used to play a story."""

    world: StoryWorld

    sound_manager: SoundManager = attrib(repr=False, init=False)
    state: WorldState = attrib()

    @state.default
    def get_default_state(instance: 'StoryLevel') -> WorldState:
        """Get a default state."""
        return WorldState(instance.world)

    def __attrs_post_init__(self) -> None:
        """Ensure all room IDs are valid."""
        if self.world.initial_room_id is None:
            raise RuntimeError(
                'You must set the initial room for your world, with a '
                '<entrance> tag inside your <world> tag.'
            )
        elif self.world.initial_room_id not in self.world.rooms:
            raise RuntimeError(
                'Invalid room id for <entrance> tag: %s.' %
                self.world.initial_room_id
            )
        room: WorldRoom
        inaccessible_rooms: List[WorldRoom] = list(self.world.rooms.values())
        for room in self.world.rooms.values():
            x: RoomExit
            for x in room.exits:
                did: str = x.destination_id
                if did not in self.world.rooms:
                    raise RuntimeError(
                        'Invalid destination %r for exit %s of room %s.' % (
                            did, x.action.name, room.name
                        )
                    )
                if x.destination in inaccessible_rooms:
                    inaccessible_rooms.remove(x.destination)
        for room in inaccessible_rooms:
            print('WARNING: There is no way to access %s!' % room.name)
        self.state.room_id = self.world.initial_room_id
        self.action('Next category', symbol=key.DOWN)(self.next_category)
        self.action('Previous category', symbol=key.UP)(self.previous_category)
        self.action('Next object', symbol=key.RIGHT)(self.next_object)
        self.action('Previous object', symbol=key.LEFT)(self.previous_object)
        self.action('Activate object', symbol=key.RETURN)(self.activate)
        return super().__attrs_post_init__()

    def on_push(self) -> None:
        """Set the sound manager up."""
        super().on_push()
        assert self.game.audio_context is not None
        self.sound_manager = SoundManager(
            self.game.audio_context, DirectSource(self.game.audio_context),
            should_loop=True
        )
        self.sound_manager.gain = self.game.config.sound.ambiance_volume.value
        self.set_room(self.state.room)

    def next_category(self) -> Generator[None, None, None]:
        """Next information category."""
        yield from self.cycle_category(1)

    def previous_category(self) -> Generator[None, None, None]:
        """Previous information category."""
        yield from self.cycle_category(-1)

    def cycle_category(self, direction: int) -> Generator[None, None, None]:
        """Cycle through information categories."""
        self.state.category_index = (
            self.state.category_index + direction
        ) % len(StoryStateCategories)
        category: StoryStateCategories = self.state.category
        category_name: str
        if category is StoryStateCategories.room:
            category_name = self.world.messages.room_category
        elif category is StoryStateCategories.objects:
            category_name = self.world.messages.objects_category
        else:
            category_name = self.world.messages.exits_category
        self.state.object_index = None
        self.game.output(category_name)
        yield
        self.next_object()

    def next_object(self) -> None:
        """Go to the next object."""
        self.cycle_object(1)

    def previous_object(self) -> None:
        """Go to the previous object."""
        self.cycle_object(-1)

    def cycle_object(self, direction: int) -> None:
        """Cycle through objects."""
        data: List[str]
        room: WorldRoom = self.state.room
        category: StoryStateCategories = self.state.category
        if category is StoryStateCategories.room:
            data = [room.name, room.description]
        elif category is StoryStateCategories.objects:
            data = [o.name for o in room.objects.values()]
        else:
            data = [x.action.name for x in room.exits]
        if not data:
            message: str = 'If you are seeing this, you have found a bug.'
            if category is StoryStateCategories.objects:
                message = self.world.messages.no_objects
            elif category is StoryStateCategories.exits:
                message = self.world.messages.no_exits
            self.game.output(message)
        else:
            index: int
            if self.state.object_index is None:
                index = 0
            else:
                index = max(0, self.state.object_index + direction)
            if index >= len(data):
                index = len(data) - 1
            self.state.object_index = index
            self.game.output(data[self.state.object_index])

    def use_exit(self, x: RoomExit) -> None:
        """Use the given exit."""
        a: WorldAction = x.action
        self.game.output(a.message)
        self.set_room(x.destination)

    def set_room(self, room: WorldRoom) -> None:
        """Move to a new room."""
        self.state.room_id = room.id
        self.state.object_index = None
        self.state.category_index = 0
        self.stop_ambiances()
        self.ambiances.clear()
        ambiance_paths: List[str] = [a.path for a in room.ambiances]
        loaded_paths: List[str] = []
        track: Track
        for track in self.tracks.copy():
            if track.path not in ambiance_paths:
                self.tracks.remove(track)
                track.stop()
            else:
                loaded_paths.append(track.path)
        a: WorldAmbiance
        for a in room.ambiances:
            path_str: str = str(a.path)
            if path_str not in loaded_paths:
                track: Track = Track('file', path_str, TrackTypes.ambiance)
                self.tracks.append(track)
                track.play(self.sound_manager)

    def perform_action(
        self, obj: RoomObject, action: WorldAction
    ) -> Callable[[], None]:
        """Return a function that will perform actions."""

        def inner() -> None:
            """Actually perform the action."""
            self.game.output(action.message)
            if action.sound is not None:
                self.game.interface_sound_manager.play_path(action.sound, True)
            self.game.pop_level()

        return inner

    def object_actions(self, obj: RoomObject) -> None:
        """Show a menu of object actions."""
        if not obj.actions:
            return self.game.output(self.world.messages.no_actions)
        m: Menu = Menu(
            self.game, self.world.messages.actions_menu.format(obj.name)
        )
        action: WorldAction
        for action in obj.actions:
            m.add_item(self.perform_action(obj, action), title=action.name)
        self.game.push_level(m)

    def activate(self) -> None:
        """Activate the currently focussed object."""
        room: WorldRoom = self.state.room
        category: StoryStateCategories = self.state.category
        if category is StoryStateCategories.room:
            self.game.output(self.world.messages.room_activate)
        elif category is StoryStateCategories.exits:
            if room.exits:
                x: RoomExit = room.exits[self.state.object_index]
                self.use_exit(x)
            else:
                self.game.output(self.world.messages.no_exits)
        else:
            if room.objects:
                obj: RoomObject = list(
                    room.objects.values()
                )[self.state.object_index]
                self.object_actions(obj)
            else:
                self.game.output(self.world.messages.no_objects)

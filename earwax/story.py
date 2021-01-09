"""Provides classes related to XML stories."""

import os.path
from enum import Enum
from pathlib import Path
from typing import (TYPE_CHECKING, Callable, Dict, Generator, List, Optional,
                    Type, Union)
from xml.dom.minidom import Document, parseString
from xml.etree.ElementTree import Element, tostring

from attr import Factory, attrib, attrs

from .ambiance import Ambiance
from .menu import Menu
from .point import Point
from .sound import Sound, SoundManager
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

if TYPE_CHECKING:
    from .story_context import StoryContext


def get_element(
    tag: str, text: Optional[str] = None, attrib: Dict[str, str] = {}
) -> Element:
    """Return a fully-formed element.

    :param tag: The XML tag t use.
    :param text: The text contained by this element.

    :param attrib: The extra attributes for the element.
    """
    e: Element = Element(tag, attrib=attrib)
    e.text = text
    return e


class StoryWorldBase:
    """Allows dumping to XML."""

    def to_xml(self) -> Element:
        """Dump this object to XML."""
        raise NotImplementedError

    def to_document(self) -> Document:
        """Return this object as an XML document."""
        s: bytes = tostring(self.to_xml())
        return parseString(s)

    def to_string(self) -> str:
        """Return this object as pretty-printed XML."""
        d: Document = self.to_document()
        return d.toprettyxml()


@attrs(auto_attribs=True)
class WorldAmbiance(StoryWorldBase):
    """An ambiance."""

    path: str

    def to_xml(self) -> Element:
        """Dump this ambiance."""
        return get_element('ambiance', text=self.path)


@attrs(auto_attribs=True)
class WorldAction(StoryWorldBase):
    """An action that can be performed.

    This class is used on objects, and when walking through doors.
    """

    name: str = 'Unnamed Action'
    message: Optional[str] = None
    sound: Optional[str] = None

    def to_xml(self) -> Element:
        """Dump this object."""
        e: Element = get_element('action')
        e.append(get_element('name', text=self.name))
        if self.message is not None:
            e.append(get_element('message', text=self.message))
        if self.sound is not None:
            e.append(get_element('sound', text=self.sound))
        return e


@attrs(auto_attribs=True)
class RoomObject(StoryWorldBase):
    """An object in the story.

    Will either sit in a room, or be in the player's inventory.
    """

    id: str
    location: 'WorldRoom'
    position: Optional[Point] = None
    name: str = 'Unnamed Object'
    ambiances: List[WorldAmbiance] = Factory(list)
    actions: List[WorldAction] = Factory(list)

    def to_xml(self) -> Element:
        """Dump this object."""
        e: Element = get_element('object')
        if self.position is not None:
            e.attrib = {
                'x': str(self.position.x),
                'y': str(self.position.y),
                'z': str(self.position.y)
            }
        e.attrib['id'] = self.id
        e.append(get_element('name', text=self.name))
        ambiance: WorldAmbiance
        for ambiance in self.ambiances:
            e.append(ambiance.to_xml())
        action: WorldAction
        for action in self.actions:
            e.append(action.to_xml())
        return e


@attrs(auto_attribs=True)
class RoomExit(StoryWorldBase):
    """An exit between two rooms."""

    location: 'WorldRoom'
    destination_id: str
    action: WorldAction = Factory(WorldAction)

    @property
    def destination(self) -> 'WorldRoom':
        """Return the room this exit leads from."""
        return self.location.world.rooms[self.destination_id]

    def to_xml(self) -> Element:
        """Dump this exit."""
        e: Element = get_element(
            'exit', attrib={'destination': self.destination_id}
        )
        e.append(self.action.to_xml())
        return e


@attrs(auto_attribs=True)
class WorldRoom(StoryWorldBase):
    """A room in a world."""

    world: 'StoryWorld'
    id: str
    name: str = 'Unnamed Room'
    description: str = 'Not described.'
    ambiances: List[WorldAmbiance] = Factory(list)
    objects: Dict[str, RoomObject] = Factory(dict)
    exits: List[RoomExit] = Factory(list)

    def get_name(self) -> str:
        """Return the actual name of this room."""
        name: str = self.name
        if name.startswith('#'):
            name = name[1:]
            if name in self.world.rooms:
                return self.world.rooms[name].name
            return f'!! ERROR: Invalid room ID {name} !!'
        return name

    def get_description(self) -> str:
        """Return the actual description of this room."""
        description: str = self.description
        if description.startswith('#'):
            description = description[1:]
            if description in self.world.rooms:
                return self.world.rooms[description].description
            return f'!! ERROR: Invalid room ID {description} !!'
        return description

    def to_xml(self) -> Element:
        """Dump this room."""
        e: Element = get_element('room', attrib={'id': self.id})
        e.append(get_element('name', text=self.name))
        e.append(get_element('description', text=self.description))
        ambiance: WorldAmbiance
        for ambiance in self.ambiances:
            e.append(ambiance.to_xml())
        obj: RoomObject
        for obj in self.objects.values():
            e.append(obj.to_xml())
        x: RoomExit
        for x in self.exits:
            e.append(x.to_xml())
        return e


@attrs(auto_attribs=True)
class WorldMessages(StoryWorldBase):
    """All the messages that can be shown to the player."""

    no_objects: str = 'This room is empty.'
    no_actions: str = 'There is nothing you can do with this object.'
    actions_menu: str = 'You step up to {}.'
    no_exits: str = 'There is no way out of this room.'
    room_activate: str = 'You cannot do that.'
    room_category: str = 'Location'
    objects_category: str = 'Objects'
    exits_category: str = 'Exits'
    main_menu: str = 'Main Menu'
    play_game: str = 'Play'
    show_credits: str = 'Show Credits'
    credits_menu: str = 'Credits'
    welcome: str = 'Welcome to this game.'
    exit: str = 'Exit'


@attrs(auto_attribs=True)
class StoryWorld(StoryWorldBase):
    """The top level world object."""

    name: str = 'Untitled World'
    author: str = 'Unknown'

    main_menu_musics: List[str] = Factory(list)
    rooms: Dict[str, WorldRoom] = Factory(dict)
    initial_room_id: Optional[str] = None
    messages: WorldMessages = Factory(WorldMessages)

    @property
    def initial_room(self) -> Optional[WorldRoom]:
        """Return the initial room for this world."""
        return self.rooms[self.initial_room_id]

    def to_xml(self) -> Element:
        """Dump this world."""
        e: Element = get_element('world')
        e.append(get_element('name', text=self.name))
        e.append(get_element('author', text=self.author))
        music: str
        for music in self.main_menu_musics:
            e.append(get_element('menumusic', text=music))
        room: WorldRoom
        for room in self.rooms.values():
            e.append(room.to_xml())
        if self.initial_room_id is not None:
            e.append(get_element('entrance', text=self.initial_room_id))
        name: str
        type_: Type
        for name, type_ in self.messages.__annotations__.items():
            if type_ is str:
                value: str = getattr(self.messages, name)
                e.append(
                    get_element('message', text=value, attrib={'id': name})
                )
        return e


class WorldStateCategories(Enum):
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
    def category(self) -> WorldStateCategories:
        """Return the current category."""
        return list(WorldStateCategories)[self.category_index]


def set_name(
    thing: Union[StoryWorld, WorldRoom, WorldAction], element: Element
) -> None:
    """Set the world name."""
    name: Optional[str] = element.text
    if name is None:
        raise RuntimeError('Names cannot be blank.')
    thing.name = name


def set_ambiance(
    parent: Union[WorldRoom, RoomObject], element: Element
) -> None:
    """Set the ambiance for a room."""
    if element.text is None:
        raise RuntimeError(
            'You must provide a path for the ambiance of %s.' % parent.name
        )
    p: str = element.text
    if not os.path.exists(p):
        raise RuntimeError(
            'The ambiance for %s is invalid: %s.' % (parent.name, p)
        )
    a: WorldAmbiance = WorldAmbiance(element.text)
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
    p: str = element.text
    if not os.path.exists(p):
        raise RuntimeError(
            'Invalid sound for action %s: %r: Path does not exist.' % (
                action.name, p
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
        obj.position = Point(*coordinates)
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
    room: WorldRoom = WorldRoom(
        world, element.attrib.get('id', f'Room_{len(world.rooms) + 1}')
    )
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
    if element.text is None:
        raise RuntimeError('Empty description provided for %s.' % room.name)
    room.description = element.text


def make_world(parent: NoneType, element: Element) -> StoryWorld:
    """Make a StoryWorld object."""
    return StoryWorld()


world_builder: Builder[NoneType, StoryWorld] = Builder(
    make_world, name='Story', builders={'room': room_builder},
    parsers={'name': set_name}
)


@world_builder.parser('menumusic')
def set_main_menu_music(world: StoryWorld, element: Element) -> None:
    """Add some main menu music."""
    p: Optional[str] = element.text
    if p is None:
        raise RuntimeError(
            'You must provide a path to load main menu music from.'
        )
    else:
        world.main_menu_musics.append(p)


@world_builder.parser('entrance')
def set_entrance(world: StoryWorld, element: Element) -> None:
    """Set the initial room."""
    world.initial_room_id = element.text


@world_builder.parser('author')
def set_author(world: StoryWorld, element: Element) -> None:
    """Set the author."""
    world.author = element.text


@world_builder.parser('message')
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

    world_context: 'StoryContext'

    sound_manager: SoundManager = attrib(repr=False, init=False)
    action_sounds: List[Sound] = Factory(list)

    def __attrs_post_init__(self) -> None:
        """Bind actions."""
        self.action('Next category', symbol=key.DOWN)(self.next_category)
        self.action('Previous category', symbol=key.UP)(self.previous_category)
        self.action('Next object', symbol=key.RIGHT)(self.next_object)
        self.action('Previous object', symbol=key.LEFT)(self.previous_object)
        self.action('Activate object', symbol=key.RETURN)(self.activate)
        self.action('Return to main menu', symbol=key.ESCAPE)(self.main_menu)
        self.action('Play or pause sounds', symbol=key.P)(self.pause)
        self.action(
            'Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT
        )(self.game.push_action_menu)
        return super().__attrs_post_init__()

    def pause(self) -> None:
        """Pause stuff."""
        a: Ambiance
        for a in self.ambiances:
            a.sound.paused = not a.sound.paused
        t: Track
        for t in self.tracks:
            t.sound.paused = not t.sound.paused
        s: Sound
        for s in self.action_sounds:
            s.paused = not s.paused

    @property
    def state(self) -> WorldState:
        """Return the current state."""
        return self.world_context.state

    @property
    def world(self) -> StoryWorld:
        """Get the attached world."""
        return self.world_context.world

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

    def main_menu(self) -> None:
        """Return to the main menu."""
        self.game.replace_level(self.world_context.get_main_menu())

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
        ) % len(WorldStateCategories)
        category: WorldStateCategories = self.state.category
        category_name: str
        if category is WorldStateCategories.room:
            category_name = self.world.messages.room_category
        elif category is WorldStateCategories.objects:
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
        category: WorldStateCategories = self.state.category
        if category is WorldStateCategories.room:
            data = [room.get_name(), room.get_description()]
        elif category is WorldStateCategories.objects:
            data = [o.name for o in room.objects.values()]
        else:
            data = [x.action.name for x in room.exits]
        if not data:
            message: str = 'If you are seeing this, you have found a bug.'
            if category is WorldStateCategories.objects:
                message = self.world.messages.no_objects
            elif category is WorldStateCategories.exits:
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
        if a.sound is not None:
            self.game.interface_sound_manager.play_path(Path(a.sound), True)
        self.set_room(x.destination)

    def set_room(self, room: WorldRoom) -> None:
        """Move to a new room."""
        self.state.room_id = room.id
        self.state.object_index = None
        self.state.category_index = 0
        while self.action_sounds:
            s: Sound = self.action_sounds.pop()
            s.destroy(destroy_source=True)
        self.stop_ambiances()
        self.ambiances.clear()
        obj: RoomObject
        a: WorldAmbiance
        for obj in room.objects.values():
            for a in obj.ambiances:
                ambiance: Ambiance = Ambiance('file', a.path, obj.position)
                self.ambiances.append(ambiance)
        self.start_ambiances()
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
                source: Source3D = Source3D(self.game.audio_context)
                source.gain = self.game.config.sound.ambiance_volume.value
                source.position = obj.position.coordinates
                s: Sound = Sound.from_path(
                    self.game.audio_context, source, self.game.buffer_cache,
                    Path(action.sound)
                )
                self.action_sounds.append(s)
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
        category: WorldStateCategories = self.state.category
        if category is WorldStateCategories.room:
            self.game.output(self.world.messages.room_activate)
        elif category is WorldStateCategories.exits:
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

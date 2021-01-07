"""Provides classes related to XML stories."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from xml.etree.ElementTree import Element

from attr import Factory, attrib, attrs
from pyglet.window import key
from shortuuid import uuid
from xml_python import Builder, NoneType

from .level import Level


@attrs(auto_attribs=True)
class StorySound:
    """A sound which is heard when something happens in the story."""

    path: Path


@attrs(auto_attribs=True)
class StoryAmbiance(StorySound):
    """An ambiance."""

    position: Optional[Tuple[float, float, float]] = None


@attrs(auto_attribs=True)
class StoryAction:
    """An action that can be performed.

    This class is used on objects, and when walking through doors.
    """

    name: str = 'Unnamed Action'
    message: Optional[str] = None
    sound: Optional[StorySound] = None


@attrs(auto_attribs=True)
class StoryObject:
    """An object in the story.

    Will either sit in a room, or be in the player's inventory.
    """

    id: str
    location: 'StoryRoom'
    position: Optional[Tuple[float, float, float]] = None
    name: str = 'Unnamed Object'
    ambiance: Optional[StoryAmbiance] = None
    actions: List[StoryAction] = Factory(list)


@attrs(auto_attribs=True)
class StoryRoomExit:
    """An exit between two rooms."""

    location: 'StoryRoom'
    destination_id: str
    action: StoryAction = Factory(StoryAction)

    @property
    def destination(self) -> 'StoryRoom':
        """Return the room this exit leads from."""
        return self.location.world.rooms[self.destination_id]


@attrs(auto_attribs=True)
class StoryRoom:
    """A room in a world."""

    world: 'StoryWorld'
    id: str
    name: str = 'Unnamed Room'
    description: str = 'Not described.'
    ambiance: Optional[StoryAmbiance] = None
    objects: Dict[str, StoryObject] = Factory(dict)
    exits: List[StoryRoomExit] = Factory(list)


@attrs(auto_attribs=True)
class StoryWorld:
    """The top level world object."""

    name: str = 'Untitled World'
    author: str = 'Unknown'

    rooms: Dict[str, StoryRoom] = Factory(dict)
    initial_room_id: Optional[str] = None

    @property
    def initial_room(self) -> Optional[StoryRoom]:
        """Return the initial room for this world."""
        return self.rooms[self.initial_room_id]


@attrs(auto_attribs=True)
class StoryState:
    """The state of a story."""

    world: StoryWorld

    room_id: Optional[str] = None
    inventory_ids: List[str] = Factory(list)
    tab_index: int = Factory(int)
    arrow_index: int = Factory(int)

    @property
    def room(self) -> StoryRoom:
        """Get the current room."""
        return self.world.rooms[self.room_id]


def set_name(
    thing: Union[StoryWorld, StoryRoom, StoryAction], element: Element
) -> None:
    """Set the world name."""
    thing.name = element.text


def set_ambiance(
    parent: Union[StoryRoom, StoryObject], element: Element
) -> None:
    """Set the ambiance for a room."""
    a: StoryAmbiance = StoryAmbiance(element.text)
    if isinstance(parent, StoryObject):
        a.position = parent.position
    parent.ambiance = a


def make_action(
    obj: Union[StoryRoomExit, StoryObject], element: Element
) -> StoryAction:
    """Make a new action."""
    action: StoryAction = StoryAction()
    if isinstance(obj, StoryRoomExit):
        obj.action = action
    elif isinstance(obj, StoryObject):
        obj.actions.append(action)
    else:
        raise RuntimeError('Invalid action placement: below object %r.' % obj)
    return action


action_builder: Builder[
    Union[StoryObject, StoryRoomExit], StoryAction
] = Builder(
    make_action, name='Action', parsers={
        'name': set_name,
    }
)


@action_builder.parser('message')
def set_message(action: StoryAction, element: Element) -> None:
    """Set the action message."""
    action.message = element.text


@action_builder.parser('sound')
def set_sound(action: StoryAction, element: Element) -> None:
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


def make_object(room: StoryRoom, element: Element) -> StoryObject:
    """Make a story object instance."""
    obj: StoryObject = StoryObject(element.attrib.get('str', uuid()), room)
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
    return obj


object_builder: Builder[StoryRoom, StoryObject] = Builder(
    make_object, name='Object', parsers={
        'name': set_name,
        'ambiance': set_ambiance
    }, builders={
        'action': action_builder
    }
)


def make_exit(room: StoryRoom, element: Element) -> StoryRoomExit:
    """Make a room exit."""
    destination_id: Optional[str] = element.attrib.get('destination', None)
    if destination_id is None:
        raise RuntimeError(
            'Cannot make exit from room %s with no destination id.' % room.name
        )
    x: StoryRoomExit = StoryRoomExit(room, destination_id)
    room.exits.append(x)
    return x


exit_builder: Builder[StoryRoom, StoryRoomExit] = Builder(
    make_exit, name='Exit', builders={
        'action': action_builder
    }
)


def make_room(world: StoryWorld, element: Element) -> StoryRoom:
    """Make a new room."""
    room: StoryRoom = StoryRoom(world, element.attrib.get('id', uuid()))
    world.rooms[room.id] = room
    return room


room_builder: Builder[StoryWorld, StoryRoom] = Builder(
    make_room, name='Room', parsers={
        'name': set_name,
        'ambiance': set_ambiance
    }, builders={
        'object': object_builder,
        'exit': exit_builder
    }
)


@room_builder.parser('description')
def set_description(room: StoryRoom, element: Element) -> None:
    """Set the description."""
    if element.text is not None:
        room.description = element.text


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


@attrs(auto_attribs=True)
class StoryLevel(Level):
    """A level that can be used to play a story."""

    world: StoryWorld

    state: StoryState = attrib()

    @state.default
    def get_default_state(instance: 'StoryLevel') -> StoryState:
        """Get a default state."""
        return StoryState(instance.world)

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
        room: StoryRoom
        for room in self.world.rooms.values():
            x: StoryRoomExit
            for x in room.exits:
                did: str = x.destination_id
                if did not in self.world.rooms:
                    raise RuntimeError(
                        'Invalid destination %r for exit %s of room %s.' % (
                            did, x.action.name, room.name
                        )
                    )
        self.state.room_id = self.world.initial_room_id
        self.action('Next category', symbol=key.TAB)(self.next_category)
        self.action(
            'Previous category', symbol=key.TAB, modifiers=key.MOD_SHIFT
        )(self.previous_category)
        self.action('Next object', symbol=key.RIGHT)(self.next_object)
        self.action('Previous object', symbol=key.LEFT)(self.previous_object)
        return super().__attrs_post_init__()

    def next_category(self) -> None:
        """Next information category."""
        self.cycle_category(1)

    def previous_category(self) -> None:
        """Previous information category."""
        self.cycle_category(-1)

    def cycle_category(self, direction: int) -> None:
        """Cycle through information categories."""
        self.game.output(str(direction))

    def next_object(self) -> None:
        """Go to the next object."""
        self.cycle_object(1)

    def previous_object(self) -> None:
        """Go to the previous object."""
        self.cycle_object(-1)

    def cycle_object(self, direction: int) -> None:
        """Cycle through objects."""
        self.game.output(str(direction))

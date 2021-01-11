"""Provides builders for the various story classes."""

import os.path
from html import unescape
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree.ElementTree import Element

from shortuuid import uuid
from xml_python import Builder
from yaml import load

from ..credit import Credit

try:
    from yaml import CLoader
except ImportError:
    from yaml import FullLoader as CLoader  # type: ignore[misc]

from ..game import Game
from ..point import Point
from .world import (RoomExit, RoomObject, RoomObjectTypes, StoryWorld,
                    WorldAction, WorldAmbiance, WorldRoom)

NoneType = type(None)


def set_name(
    thing: Union[StoryWorld, WorldRoom, WorldAction, Credit],
    element: Element
) -> None:
    """Set the world name."""
    name: Optional[str] = element.text
    if name is None:
        raise RuntimeError('Names cannot be blank.')
    thing.name = unescape(name)


def set_ambiance(
    parent: Union[WorldRoom, RoomObject], element: Element
) -> None:
    """Set the ambiance for a room."""
    if element.text is None:
        raise RuntimeError(
            'You must provide a path for the ambiance of %s.' % parent.name
        )
    p: str = unescape(element.text)
    if not os.path.exists(p):
        raise RuntimeError(
            'The ambiance for %s is invalid: %s.' % (parent.name, p)
        )
    a: WorldAmbiance = WorldAmbiance(element.text)
    parent.ambiances.append(a)


def make_action(
    obj: Union[RoomExit, RoomObject, StoryWorld], element: Element
) -> WorldAction:
    """Make a new action."""
    action: WorldAction = WorldAction()
    if isinstance(obj, RoomExit):
        obj.action = action
    elif isinstance(obj, RoomObject):
        if element.tag == 'action':
            obj.actions.append(action)
        elif element.tag == 'mainaction':
            obj.actions_action = action
            action.name = 'Main'
        elif element.tag == 'dropaction':
            obj.drop_action = action
            action.name = 'Drop'
        elif element.tag == 'takeaction':
            obj.take_action = action
            action.name = 'Take'
        elif element.tag == 'useaction':
            obj.use_action = action
            action.name = 'Use'
        else:
            raise RuntimeError('Invalid action tag: <%s>.' % element.tag)
    elif isinstance(obj, StoryWorld):
        if element.tag == 'dropaction':
            obj.drop_action = action
            action.name = obj.drop_action.name
        elif element.tag == 'takeaction':
            obj.take_action = action
            action.name = obj.take_action.name
        else:
            raise RuntimeError('Invalid action tag: <%s>.' % element.tag)
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
    if action.message is not None:
        action.message = unescape(action.message)


@action_builder.parser('sound')
def set_sound(obj: Union[WorldAction, Credit], element: Element) -> None:
    """Set the action sound."""
    type_name: str
    if isinstance(obj, WorldAction):
        type_name = 'action'
    else:
        assert isinstance(obj, Credit)
        type_name = 'credit'
    if element.text is None:
        raise RuntimeError(f'Empty sound tag for {type_name} {obj.name}.')
    p: str = unescape(element.text)
    if not os.path.exists(p):
        raise RuntimeError(
            f'Invalid sound for {type_name} {obj.name}: {p!r}: '
            'Path does not exist.'
        )
    if isinstance(obj, Credit):
        obj.sound = Path(p)
    else:
        obj.sound = p


def make_object(room: WorldRoom, element: Element) -> RoomObject:
    """Make a story object instance."""
    obj: RoomObject = RoomObject(element.attrib.get('id', uuid()), room)
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
        'action': action_builder,
        'mainaction': action_builder,
        'takeaction': action_builder,
        'dropaction': action_builder,
        'useaction': action_builder,
    }
)


@object_builder.parser('type')
def set_type(obj: RoomObject, element: Element) -> None:
    """Set the type of an object."""
    if element.text is None:
        raise RuntimeError(
            'Empty <type> tag received for object %s.' % obj.name
        )
    elif element.text not in RoomObjectTypes.__members__:
        raise RuntimeError(
            'Invalid object type for %s: %s.' % (obj.name, element.text)
        )
    obj.type = RoomObjectTypes.__members__[element.text]


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
    world.add_room(room)
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
    room.description = unescape(element.text)


def make_credit(world: StoryWorld, element: Element) -> Credit:
    """Make a new credit."""
    c: Credit = Credit.earwax_credit()
    world.game.credits.append(c)
    return c


credit_builder: Builder[StoryWorld, Credit] = Builder(
    make_credit, name='Credit', parsers={
        'name': set_name,
        'sound': set_sound
    }
)


@credit_builder.parser('url')
def set_url(credit: Credit, element: Element) -> None:
    """Set the URL."""
    if element.text is None:
        raise RuntimeError(
            'An empty URL was provided for the %s credit.' % credit.name
        )
    credit.url = element.text


def make_world(parent: Game, element: Element) -> StoryWorld:
    """Make a StoryWorld object."""
    return StoryWorld(parent)


world_builder: Builder[Game, StoryWorld] = Builder(
    make_world, name='Story', builders={
        'room': room_builder,
        'credit': credit_builder,
        'dropaction': action_builder,
        'takeaction': action_builder
    },
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
    p = unescape(p)
    if not os.path.isfile(p):
        raise RuntimeError('Invalid music path: %s. path does not exist.' % p)
    world.main_menu_musics.append(p)


@world_builder.parser('entrance')
def set_entrance(world: StoryWorld, element: Element) -> None:
    """Set the initial room."""
    rid: Optional[str] = element.text
    if rid is None:
        raise RuntimeError('Empty <entrance> tag provided.')
    world.initial_room_id = unescape(rid)


@world_builder.parser('author')
def set_author(world: StoryWorld, element: Element) -> None:
    """Set the author."""
    if element.text is None:
        raise RuntimeError('The author tag cannot be empty.')
    world.author = unescape(element.text)


@world_builder.parser('message')
def set_world_message(world: StoryWorld, element: Element) -> None:
    """Set a message on the world."""
    message_ids: List[str] = list(world.messages.__annotations__)
    message_id: Optional[str] = element.attrib.get('id', None)
    if message_id is None:
        raise RuntimeError('All world messages must have IDs.')
    message_id = unescape(message_id)
    if message_id not in message_ids:
        raise RuntimeError(
            'Invalid message ID %r. Valid IDs: %s' % (
                message_id, ', '.join(message_ids)
            )
        )
    if element.text is None:
        raise RuntimeError('Tried to blank the %r message.' % message_id)
    setattr(world.messages, message_id, unescape(element.text))


@world_builder.parser('config')
def set_config(world: StoryWorld, element: Element) -> None:
    """Load Earwax configuration."""
    if element.text is None:
        raise RuntimeError('Empty <config> tag supplied.')
    text: str = unescape(element.text)
    data: Dict[str, Any] = load(text, Loader=CLoader)
    world.game.config.populate_from_dict(data)


@world_builder.parser('cursorsound')
def set_cursor_sound(world: StoryWorld, element: Element) -> None:
    """Set the cursor sound."""
    if element.text is None:
        raise RuntimeError('Empty cursor sound value provided.')
    elif not os.path.exists(element.text):
        raise RuntimeError(
            'Invalid cursor sound provided: %s. Path does not exist.' %
            element.text
        )
    world.cursor_sound = element.text

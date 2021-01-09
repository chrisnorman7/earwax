"""Provides builders for the various story classes."""

import os.path
from typing import List, Optional, Union
from xml.etree.ElementTree import Element

from shortuuid import uuid
from xml_python import Builder

from ..point import Point
from .world import (RoomExit, RoomObject, StoryWorld, WorldAction,
                    WorldAmbiance, WorldRoom)

NoneType = type(None)


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

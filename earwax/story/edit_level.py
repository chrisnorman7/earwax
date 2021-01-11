"""Provides the EditLevel class."""

import os.path
from inspect import isgenerator
from typing import Callable, Dict, Generator, List, Optional, Union, cast

from attr import Attribute, attrs
from shortuuid import uuid

from ..editor import Editor
from ..game import Game
from ..level import Level
from ..menu import Menu
from ..types import OptionalGenerator
from .play_level import PlayLevel
from .world import (ObjectTypes, RoomExit, RoomObject, WorldAction,
                    WorldAmbiance, WorldMessages, WorldRoom)

try:
    from pyglet.window import key
except ModuleNotFoundError:
    key = None

message_descriptions: Dict[str, str] = {
    'no_objects': 'The message shown when focusing an empty object list',
    'no_actions': 'The message which is shown when there are no object '
    'actions',
    'no_exits': 'The message which is shown when focusing an empty exit list',
    'room_activate': 'The message which is shown when trying to activate a '
    'room name or description',
    'room_category': 'The name of the room category',
    'objects_category': 'The name of the objects category',
    'exits_category': 'The name of the exits category',
    'actions_menu': 'The default title of the object actions menu',
    'main_menu': 'The title of the main menu',
    'play_game': 'The title of the play game entry of the main menu',
    'load_game': 'The title of the load game entry of the main menu',
    'exit': 'The title of the exit entry of the main menu',
    'credits_menu': 'The title of the credits menu',
    'show_credits': 'The title of the show credits entry of the main menu',
    'welcome': 'The welcome message',
    'no_saved_game': 'The message which is spoken when there is no saved game'
}


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
        self.action('Creation menu', symbol=key.C)(self.create_menu)
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
        self.action(
            'Change world message', symbol=key.M, modifiers=key.MOD_SHIFT
        )(self.set_world_messages)
        self.action('Sounds menu', symbol=key.S)(self.sounds_menu)
        self.action('Ambiances menu', symbol=key.A)(self.ambiances_menu)
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
        e: Editor = Editor(self.game, text=action.message or '')

        @e.event
        def on_submit(text: str) -> None:
            """Set the message."""
            action.message = text
            if text == '':
                action.message = None
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
            level: Optional[Level] = self.game.level
            assert isinstance(level, Menu)

            def inner() -> Generator[None, None, None]:
                """Set ``obj.actions_action.message``."""
                assert isinstance(obj, RoomObject)
                if obj.actions_action is None:
                    obj.actions_action = WorldAction(name='Main Action')
                self.game.pop_level()
                yield from self.set_message(obj.actions_action)

            level.add_item(inner, title='Object Actions Message')

    def set_world_messages(self) -> Generator[None, None, None]:
        """Push a menu that allows the editing of world messages."""
        yield
        messages: WorldMessages = self.world.messages
        m: Menu = Menu(self.game, 'World Messages')
        value: str
        a: Attribute
        for a in messages.__attrs_attrs__:  # type: ignore[attr-defined]
            if a.type is not str:
                continue
            value = getattr(self.world.messages, a.name)
            assert isinstance(value, str)

            def inner(
                name: str = a.name, value: str = value,
                default: str = cast(str, a.default)
            ) -> Generator[None, None, None]:
                """Edit the message."""
                e: Editor = Editor(self.game, text=value)

                @e.event
                def on_submit(text: str) -> None:
                    """Set the value."""
                    self.game.pop_level()
                    if not text:
                        text = default
                    setattr(self.world.messages, name, text)
                    self.game.output('Message set.')

                self.game.pop_level()
                self.game.output('Enter the message: %s' % value)
                yield
                self.game.push_level(e)

            title: str = message_descriptions.get(a.name, a.name)
            title = f'{title}: {value!r}'
            m.add_item(inner, title=title)
        self.game.push_level(m)

    def set_sound(self, action: WorldAction) -> Generator[None, None, None]:
        """Set the sound on the given action.

        :param action: The action whose sound will be changed.
        """
        e: Editor = Editor(self.game, text=action.sound or '')

        @e.event
        def on_submit(text: str) -> None:
            """Set the sound."""
            if text:
                if os.path.exists(text):
                    self.game.pop_level()
                    action.sound = text
                    self.game.output('Sound set.')
                    self.play_action_sound(text)
                else:
                    self.game.output('Path does not exist: %s.' % text)
                    e.text = text
            else:
                self.game.pop_level()
                action.sound = None
                self.game.output('Sound cleared.')

        self.game.output(
            'Enter a new sound for %s: %s' % (action.name, action.sound)
        )
        yield
        self.game.push_level(e)

    def set_cursor_sound(self) -> Generator[None, None, None]:
        """Set the cursor sound."""
        sound: str = ''
        if self.world.cursor_sound is not None:
            sound = self.world.cursor_sound
        e: Editor = Editor(self.game, text=sound)

        @e.event
        def on_submit(text: str) -> None:
            self.game.pop_level()
            if not text:
                self.world.cursor_sound = None
                self.game.output('Cursor sound cleared.')
            elif not os.path.exists(text):
                self.game.output('Pat does not exist: %s.' % text)
            else:
                self.world.cursor_sound = text
                self.game.output('Cursor sound set.')

        self.game.output(
            'Enter a new path for the cursor sound: %s' %
            self.world.cursor_sound
        )
        yield
        self.game.push_level(e)

    def sounds_menu(self) -> OptionalGenerator:
        """Add or remove ambiances for the currently focused object."""
        obj: Optional[ObjectTypes] = self.object
        if isinstance(obj, RoomExit):
            yield from self.set_sound(obj.action)
        elif isinstance(obj, RoomObject):
            yield
            push_actions_menu(self.game, obj.actions, self.set_sound)
            assert isinstance(self.game.level, Menu)
            m: Menu = self.game.level

            def inner() -> Generator[None, None, None]:
                """Edit the main object action."""
                assert isinstance(obj, RoomObject)
                self.game.pop_level()
                if obj.actions_action is None:
                    obj.actions_action = WorldAction(name='Main Action')
                yield from self.set_sound(obj.actions_action)

            m.add_item(inner, title='Main actions sound')
        elif isinstance(obj, WorldRoom):
            yield from self.set_cursor_sound()
        else:
            self.game.output('Nothing selected.')

    def add_ambiance(
        self, ambiances: List[WorldAmbiance]
    ) -> Callable[[], Generator[None, None, None]]:
        """Add a new ambiance to the given list."""

        def inner() -> Generator[None, None, None]:
            e: Editor = Editor(self.game)

            @e.event
            def on_submit(text: str) -> None:
                if not text:
                    self.game.output('Cancelled.')
                elif not os.path.exists(text):
                    self.game.output('Path does not exist: %s.' % text)
                else:
                    ambiances.append(WorldAmbiance(text))
                    self.set_room(self.room)
                    self.game.output('Done.')
                while not isinstance(self.game.level, EditLevel):
                    self.game.pop_level()

            self.game.output('Enter a path for your new ambiance')
            yield
            self.game.push_level(e)

        return inner

    def ambiance_menu(
        self, ambiances: List[WorldAmbiance], ambiance: WorldAmbiance
    ) -> Callable[[], None]:
        """Push the edit ambiance menu."""
        def inner() -> None:
            m: Menu = Menu(self.game, 'Ambiance Menu')
            m.add_item(self.edit_ambiance(ambiance), title='Edit')
            m.add_item(
                self.delete_ambiance(ambiances, ambiance), title='Delete'
            )
            self.game.push_level(m)

        return inner

    def edit_ambiance(
        self, ambiance: WorldAmbiance
    ) -> Callable[[], Generator[None, None, None]]:
        """Edit the ambiance."""

        def inner() -> Generator[None, None, None]:
            e: Editor = Editor(self.game, text=ambiance.path)

            @e.event
            def on_submit(text: str) -> None:
                """Set the new ambiance."""
                self.game.pop_level()
                if text:
                    if os.path.exists(text):
                        ambiance.path = text
                        self.game.output('Ambiance set.')
                        self.set_room(self.room)
                    else:
                        self.game.output('Path does not exist: %s.' % text)
                else:
                    self.game.output(
                        'Ambiances cannot be cleared, only deleted.'
                    )

            self.game.output('Enter a path: %s' % ambiance.path)
            yield
            self.game.push_level(e)

        return inner

    def delete_ambiance(
        self, ambiances: List[WorldAmbiance], ambiance: WorldAmbiance
    ) -> Callable[[], None]:
        """Delete the ambiance."""

        def yes() -> None:
            """Actually delete the ambiance."""
            ambiances.remove(ambiance)
            self.game.output('Deleted.')
            while not isinstance(self.game.level, EditLevel):
                self.game.pop_level()
            self.set_room(self.room)

        def no() -> None:
            """Don't delete."""
            self.game.output('Cancelled.')
            self.game.pop_level()

        def inner() -> None:
            m: Menu = Menu.yes_no(self.game, yes, no)
            self.game.push_level(m)

        return inner

    def ambiances_menu(self) -> None:
        """Push a menu that can edit ambiances."""
        obj: Optional[ObjectTypes] = self.object
        if obj is None:
            self.game.output('Nothing selected.')
        elif isinstance(obj, RoomExit):
            self.game.output(
                'Exits do not have ambiances. Perhaps you wanted to edit the '
                'exit sound with the S key?'
            )
        else:
            assert isinstance(obj, (WorldRoom, RoomObject))
            m: Menu = Menu(self.game, 'Ambiances')
            m.add_item(self.add_ambiance(obj.ambiances), title='Add')
            a: WorldAmbiance
            for a in obj.ambiances:
                m.add_item(
                    self.ambiance_menu(obj.ambiances, a), title=a.path
                )
            self.game.push_level(m)

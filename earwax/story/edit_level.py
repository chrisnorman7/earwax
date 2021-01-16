"""Provides the EditLevel class."""

import os.path
from inspect import isgenerator
from pathlib import Path
from typing import (Callable, Dict, Generator, List, Optional, Tuple, Type,
                    Union, cast)

from attr import Attribute, attrib, attrs

from ..editor import Editor
from ..game import Game
from ..level import Level
from ..menu import Menu
from ..pyglet import key
from ..types import OptionalGenerator
from .play_level import PlayLevel
from .world import (DumpablePoint, DumpableReverb, ObjectTypes, RoomExit,
                    RoomObject, RoomObjectTypes, StoryWorld, WorldAction,
                    WorldAmbiance, WorldMessages, WorldRoom)

message_descriptions: Dict[str, str] = {
    'no_objects': 'The message shown when focusing an empty object list',
    'no_actions': 'The message which is shown when there are no object '
    'actions',
    'no_exits': 'The message which is shown when focusing an empty exit list',
    'no_use': 'The message which is shown when an object cannot be used',
    'nothing_to_use': 'The message which is shown when the player has nothing '
    'to  use',
    'nothing_to_drop': 'The message which is shown when the player has '
    'nothing to drop',
    'empty_inventory': 'The message which is shown when the player has an '
    'empty inventory',
    'room_activate': 'The message which is shown when trying to activate a '
    'room name or description',
    'room_category': 'The name of the room category',
    'objects_category': 'The name of the objects category',
    'exits_category': 'The name of the exits category',
    'actions_menu': 'The default title of the object actions menu',
    'inventory_menu': 'The title of the inventory menu',
    'main_menu': 'The title of the main menu',
    'play_game': 'The title of the play game entry of the main menu',
    'load_game': 'The title of the load game entry of the main menu',
    'exit': 'The title of the exit entry of the main menu',
    'credits_menu': 'The title of the credits menu',
    'show_credits': 'The title of the show credits entry of the main menu',
    'welcome': 'The welcome message',
    'no_saved_game': 'The message which is spoken when there is no saved game'
}


@attrs(auto_attribs=True)
class ObjectPositionLevel(Level):
    """A level for editing the position of an object.

    :ivar ~earwax.story.edit_level.ObjectPositionLevel.object: The object or
        exit whose position will be edited.

    :ivar ~earwax.story.edit_level.ObjectPositionLevel.level: The edit level
        which pushed this level.
    """

    object: Union[RoomObject, RoomExit]
    level: 'EditLevel'

    initial_position: Optional[DumpablePoint] = attrib()

    @initial_position.default
    def get_initial_position(
        instance: 'ObjectPositionLevel'
    ) -> Optional[DumpablePoint]:
        """Get the object position."""
        if instance.object.position is None:
            return instance.object.position
        return DumpablePoint(*instance.object.position.coordinates)

    def __attrs_post_init__(self) -> None:
        """Add actions."""
        keys: List[Tuple[int, Callable[[], None]]] = [
            (key.LEFT, self.left),
            (key.RIGHT, self.right),
            (key.UP, self.forward),
            (key.DOWN, self.backward),
            (key.PAGEDOWN, self.down),
            (key.PAGEUP, self.up)
        ]
        symbol: int
        func: Callable[[], None]
        for symbol, func in keys:
            self.action(func.__name__.title(), symbol=symbol)(func)
        self.action('Clear position', symbol=key.C)(self.clear)
        self.action('Finish moving', symbol=key.RETURN)(self.done)
        self.action('Cancel', symbol=key.ESCAPE)(self.cancel)
        self.action('Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT)(
            lambda: self.game.push_action_menu()
        )
        return super().__attrs_post_init__()

    def reset(self) -> None:
        """Reset the current room."""
        if self.object.position is None:
            self.game.output('Position cleared.')
        else:
            f: float
            y: float
            x: float
            x, y, z = self.object.position.floor().coordinates
            self.game.output(f'Moved to {x}, {y}, {z}.')
        self.level.play_cursor_sound(self.object.position)
        self.level.set_room(self.level.room)

    def move(self, x: int = 0, y: int = 0, z: int = 0) -> None:
        """Change the position of this object."""
        if self.object.position is None:
            self.object.position = DumpablePoint(x, y, z)
        else:
            self.object.position.x += x
            self.object.position.y += y
            self.object.position.z += z
        self.reset()

    def clear(self) -> None:
        """Clear the object position."""
        self.object.position = None
        self.reset()

    def forward(self) -> None:
        """Move the sound forwards."""
        self.move(y=1)

    def backward(self) -> None:
        """Move the sound backwards."""
        self.move(y=-1)

    def left(self) -> None:
        """Move the sound left."""
        self.move(x=-1)

    def right(self) -> None:
        """Move the sound right."""
        self.move(x=1)

    def down(self) -> None:
        """Move the sound down."""
        self.move(z=-1)

    def up(self) -> None:
        """Move the sound up."""
        self.move(z=1)

    def done(self) -> None:
        """Finish editing."""
        if self.object.position == self.initial_position:
            self.game.output('Object unmoved.')
        else:
            self.game.output('Finished editing.')
        self.game.reveal_level(self.level)

    def cancel(self) -> None:
        """Undo the move, and return everything to how it was."""
        self.object.position = self.initial_position
        self.done()


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

    filename: Optional[Path] = None

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
        self.action('Describe this room', symbol=key.E)(self.describe_room)
        self.action(
            'Shadow room description', symbol=key.E, modifiers=key.MOD_SHIFT
        )(self.shadow_description)
        self.action('Change message', symbol=key.M)(self.remessage)
        self.action(
            'Change world message', symbol=key.M, modifiers=key.MOD_SHIFT
        )(self.set_world_messages)
        self.action('Sounds menu', symbol=key.S)(self.sounds_menu)
        self.action('Change object type', symbol=key.T)(self.set_object_type)
        self.action('Ambiances menu', symbol=key.A)(self.ambiances_menu)
        self.action(
            'Actions menu', symbol=key.A, modifiers=key.MOD_SHIFT
        )(self.object_actions)
        self.action('Reposition object', symbol=key.X)(self.reposition_object)
        self.action(
            'Configure room reverb', symbol=key.V
        )(self.configure_reverb)
        self.action('Delete', symbol=key.DELETE)(self.delete)
        return super().__attrs_post_init__()

    @property
    def room(self) -> WorldRoom:
        """Return the current room."""
        return self.state.room

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
        assert self.filename is not None
        try:
            self.world.save(self.filename)
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
            room.create_exit(destination)
            self.game.output('Exit created.')

        push_rooms_menu(
            self.game, self.get_rooms(include_current=False), inner
        )

    def create_object(self) -> None:
        """Create a new object in the current room."""
        self.game.pop_level()
        room: WorldRoom = self.room
        room.create_object()
        self.game.output('Object created.')

    def create_room(self) -> None:
        """Create a new room."""
        self.game.pop_level()
        r: WorldRoom = WorldRoom()
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
                self.edit_volume_multiplier(ambiance),
                title=f'Change volume offset ({ambiance.volume_multiplier})'
            )
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

    def edit_volume_multiplier(self, ambiance: WorldAmbiance) -> Callable[
        [], Generator[None, None, None]
    ]:
        """Return a callable that can be used to set an ambiance volume multiplier.

        :param ambiance: The ambiance whose volume multiplier will be changed.
        """

        def inner() -> Generator[None, None, None]:
            e: Editor = Editor(self.game, str(ambiance.volume_multiplier))

            @e.event
            def on_submit(text: str) -> None:
                self.game.reveal_level(self)
                value: float
                if not text:
                    value = 1.0
                else:
                    try:
                        value = float(text)
                    except TypeError:
                        return self.game.output(f'Invalid value: {text}.')
                ambiance.volume_multiplier = value
                self.set_room(self.room)
                self.game.output(
                    'Volume multiplier set to %.2f'
                    % ambiance.volume_multiplier
                )

            self.game.output(
                'Enter a new value for the volume offset: %.2f' %
                ambiance.volume_multiplier
            )
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

    def ambiances_menu(self) -> Generator[None, None, None]:
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
            yield
            self.game.push_level(m)

    def reposition_object(self) -> None:
        """Reposition the currently selected object."""
        obj: Optional[ObjectTypes] = self.object
        if not isinstance(obj, (RoomObject, RoomExit)):
            return self.game.output(
                'You can only reposition objects or exits.'
            )
        position: str = 'Not set'
        if obj.position is not None:
            position = f'{obj.position.x}, {obj.position.y}, {obj.position.z}'
        name: str
        if isinstance(obj, RoomObject):
            name = obj.name
        else:
            name = obj.action.name
        self.game.output(
            f'Repositioning {name}. '
            f'Current position: {position}.'
        )
        l: ObjectPositionLevel = ObjectPositionLevel(self.game, obj, self)
        self.game.push_level(l)

    def delete(self) -> None:
        """Delete the currently focused object."""
        msg: Optional[str] = None
        obj: Optional[ObjectTypes] = self.object
        if obj is None:
            msg = 'You must first select something.'
        if isinstance(obj, WorldRoom):
            if obj.exits:
                msg = 'You cannot delete a room which has exits.'
            elif obj.objects:
                msg = 'The room must be empty before deleting.'
            elif obj is self.world.initial_room:
                msg = 'First change the initial room from the main menu.'
            elif len(self.world.rooms) == 1:
                msg = 'You cannot delete the only room.'
            else:
                r: WorldRoom
                for r in self.get_rooms():
                    if r.name.startswith('#') and r.name[1:] == obj.id:
                        msg = "First stop shadowing this room's name."
                        break
                    if (
                        r.description.startswith('#') and
                        r.description[1:] == obj.id
                    ):
                        msg = "First stop shadowing this room's description."
                        break
                    x: RoomExit
                    for x in r.exits:
                        if x.destination is obj:
                            msg = (
                                'There is an entrance to this room from '
                                f'{r.get_name()} via {x.action.name}'
                            )
        if msg is not None:
            return self.game.output(msg)

        def yes() -> None:
            if isinstance(obj, WorldRoom):
                assert self.world.initial_room is not None
                assert self.world.initial_room_id is not None
                del self.world.rooms[obj.id]
                self.state.room_id = self.world.initial_room_id
                self.set_room(self.world.initial_room)
            elif isinstance(obj, RoomExit):
                obj.location.exits.remove(obj)
            elif isinstance(obj, RoomObject):
                del obj.location.objects[obj.id]
                self.set_room(self.room)
                if obj.id in self.state.inventory_ids:
                    self.state.inventory_ids.remove(obj.id)
            else:
                self.game.output('No clue how to destroy %r.' % obj)
                return self.game.pop_level()
            self.game.pop_level()
            self.game.output('Done.')

        def no() -> None:
            self.game.output('Cancelled.')
            self.game.pop_level()

        m: Menu = Menu.yes_no(
            self.game, yes, no,
            title=f'Are you sure you want to delete {obj!s}?'
        )
        self.game.push_level(m)

    def set_object_type(self) -> None:
        """Change the type of an object."""
        types: Dict[RoomObjectTypes, str] = {
            RoomObjectTypes.stuck: 'An object which cannot be taken',
            RoomObjectTypes.takeable: 'An object which can be picked up',
            RoomObjectTypes.droppable: 'An object that can be dropped'
        }
        obj: Optional[ObjectTypes] = self.object
        if not isinstance(obj, RoomObject):
            return self.game.output('First select an object.')
        description: str = types[obj.type]
        m: Menu = Menu(self.game, f'Object Type ({description})')
        type_: RoomObjectTypes
        for type_, description in types.items():

            def inner(t: RoomObjectTypes = type_) -> None:
                assert isinstance(obj, RoomObject)
                self.game.pop_level()
                obj.type = t
                self.game.output('Object type set.')

            m.add_item(inner, title=description)
        self.game.push_level(m)

    def add_action(
        self, obj: Union[RoomObject, RoomExit, StoryWorld], name: str
    ) -> Callable[[], None]:
        """Add a new action to the given object.

        :param obj: The object to assign the new action to.

        :param name: The attribute name to use.
        """
        type_: Type = type(obj)
        assert (
            name in type_.__annotations__
            and type_.__annotations__[name] is Optional[WorldAction]
        )

        def inner() -> None:
            self.game.reveal_level(self)
            action: WorldAction = WorldAction()
            setattr(obj, name, action)
            if isinstance(obj, RoomObject):
                if action is obj.take_action:
                    action.name = 'Take'
                elif action is obj.use_action:
                    action.name = 'Use'
                elif action is obj.drop_action:
                    action.name = 'Drop'
            self.game.output('Action created.')

        return inner

    def edit_action(
        self, obj: Union[RoomObject, RoomExit, StoryWorld], action: WorldAction
    ) -> Callable[[], None]:
        """Push a menu that allows editing of the action.

        :param obj: The object the action is attached to.

        :param action: The action to edit (or delete).
        """

        def inner() -> None:

            def set_name() -> Generator[None, None, None]:
                yield from self.set_name(action)

            def set_message() -> Generator[None, None, None]:
                yield from self.set_message(action)

            def set_sound() -> Generator[None, None, None]:
                yield from self.set_sound(action)

            def delete() -> None:
                def yes() -> None:
                    self.game.reveal_level(self)
                    if isinstance(obj, StoryWorld):
                        return self.game.output(
                            'You cannot delete this action.'
                        )
                    if isinstance(obj, RoomObject):
                        if action is obj.take_action:
                            obj.take_action = None
                        elif action is obj.drop_action:
                            obj.drop_action = None
                        if isinstance(obj, RoomObject):
                            if action is obj.use_action:
                                obj.use_action = None
                            elif action in obj.actions:
                                obj.actions.remove(action)
                    elif isinstance(obj, RoomExit):
                        if action is obj.action:
                            return self.game.output(
                                'You cannot delete the exit use action.'
                            )
                    else:
                        return self.game.output(
                            f'No idea how to remove the {action.name} action '
                            f'from {obj}.'
                        )
                    self.game.output('Action deleted.')

                def no() -> None:
                    self.game.pop_level()
                    self.game.output('Cancelled.')

                m: Menu = Menu.yes_no(self.game, yes, no)
                self.game.push_level(m)

            m: Menu = Menu(self.game, 'Edit Action')
            m.add_item(set_name, title=f'Rename ({action.name})')
            m.add_item(
                set_message, title=f'Set message ({action.message})'
            )
            m.add_item(
                set_sound, title=f'Set sound ({action.sound})'
            )
            m.add_item(delete, title='Delete')
            self.game.push_level(m)

        return inner

    def object_actions(self) -> Generator[None, None, None]:
        """Push a menu that lets you configure object actions."""
        obj: Optional[
            Union[RoomObject, RoomExit, WorldRoom, StoryWorld]
        ] = self.object
        if obj is None:
            return self.game.output('You must select something.')
        name: str = 'Unknown Thing'
        if isinstance(obj, WorldRoom):
            name = 'World'
            obj = self.world

        def add() -> None:
            assert isinstance(obj, RoomObject)
            action: WorldAction = WorldAction()
            obj.actions.append(action)
            self.edit_action(obj, action)()

        m: Menu = Menu(self.game, 'Title Not Set')
        if isinstance(obj, (RoomObject, StoryWorld)):
            if obj.take_action is None:
                m.add_item(
                    self.add_action(obj, 'take_action'),
                    title='Add take action'
                )
            else:
                m.add_item(
                    self.edit_action(obj, obj.take_action),
                    title='Edit take action'
                )
            if obj.drop_action is None:
                m.add_item(
                    self.add_action(obj, 'drop_action'),
                    title='Add drop action'
                )
            else:
                m.add_item(
                    self.edit_action(obj, obj.drop_action),
                    title='Edit drop action'
                )
            if isinstance(obj, RoomObject):
                name = 'Object'
                if obj.use_action is None:
                    m.add_item(
                        self.add_action(obj, 'use_action'),
                        title='Add use action'
                    )
                else:
                    m.add_item(
                        self.edit_action(obj, obj.use_action),
                        title='Edit use action'
                    )
                m.add_item(add, title='Add Action')
                action: WorldAction
                for action in obj.actions:
                    m.add_item(
                        self.edit_action(obj, action), title=action.name
                    )
        if isinstance(obj, RoomExit):
            name = 'Exit'
            if obj.action is None:
                m.add_item(
                    self.add_action(obj, 'action'), title='Add use action'
                )
            else:
                m.add_item(
                    self.edit_action(obj, obj.action),
                    title='Edit use action'
                )
        m.title = f'{name} Actions'
        yield
        self.game.push_level(m)

    def configure_reverb(self) -> None:
        """Configure the reverb for the current room."""
        room: WorldRoom = self.state.room

        def delete_reverb() -> None:

            def yes() -> None:
                if self.reverb is not None:
                    self.reverb.destroy()
                self.reverb = None
                room.reverb = None
                self.game.output('Reverb deleted.')
                self.game.reveal_level(self)

            def no() -> None:
                self.game.output('Cancelled.')
                self.game.reveal_level(self)

            m: Menu = Menu.yes_no(self.game, yes, no)
            self.game.push_level(m)

        if room.reverb is None:
            room.reverb = DumpableReverb()
            self.set_room(room)

        m: Menu = Menu(self.game, 'Reverb')
        name: str
        value: float
        for name in DumpableReverb.__annotations__:
            m.add_item(self.game.pop_level, title=name)
        m.add_item(delete_reverb, title='Delete')
        self.game.push_level(m)

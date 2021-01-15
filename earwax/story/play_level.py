"""Provides the StoryLevel class."""

from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List,
                    Optional, Union)

from attr import Factory, attrib, attrs

from .. import hat_directions
from ..ambiance import Ambiance
from ..level import Level
from ..menu import Menu
from ..point import Point
from ..pyglet import key
from ..sound import Sound
from ..track import Track, TrackTypes
from ..yaml import CDumper, dump
from .world import (
    ObjectTypes, RoomExit, RoomObject, StoryWorld, WorldAction, WorldAmbiance,
    WorldRoom, WorldState, WorldStateCategories)

if TYPE_CHECKING:
    from .context import StoryContext


@attrs(auto_attribs=True)
class PlayLevel(Level):
    """A level that can be used to play a story.

    Instances of this class can only play stories, not edit them.

    :ivar world_context: The context that contains the world, and the state for
        this story.

    :ivar action_sounds: The sounds which were started by object actions.
    """

    world_context: 'StoryContext'

    action_sounds: List[Sound] = attrib(
        default=Factory(list), init=False, repr=False
    )
    cursor_sound: Optional[Sound] = None
    inventory: List[RoomObject] = Factory(list)

    def __attrs_post_init__(self) -> None:
        """Load inventory and bind actions."""
        self.build_inventory()
        self.action(
            'Next category', symbol=key.DOWN, hat_direction=hat_directions.DOWN
        )(self.next_category)
        self.action(
            'Previous category', symbol=key.UP, hat_direction=hat_directions.UP
        )(self.previous_category)
        self.action(
            'Next object', symbol=key.RIGHT, hat_direction=hat_directions.RIGHT
        )(self.next_object)
        self.action(
            'Previous object', symbol=key.LEFT,
            hat_direction=hat_directions.LEFT
        )(self.previous_object)
        self.action(
            'Activate object', symbol=key.RETURN, joystick_button=0
        )(self.activate)
        self.action(
            'Inventory', symbol=key.I, joystick_button=3
        )(self.inventory_menu)
        self.action(
            'Use object', symbol=key.U, joystick_button=2
        )(self.use_object_menu)
        self.action(
            'Drop object', symbol=key.D, joystick_button=1
        )(self.drop_object_menu)
        self.action(
            'Return to main menu', symbol=key.Q, joystick_button=9
        )(self.main_menu)
        self.action('Play or pause sounds', symbol=key.P)(self.pause)
        self.action(
            'Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT,
            joystick_button=6
        )(self.game.push_action_menu)
        self.action(
            'Volume down', symbol=key.PAGEDOWN, interval=0.1, joystick_button=4
        )(
            self.game.change_volume(-0.05)
        )
        self.action(
            'Volume Up', symbol=key.PAGEUP, interval=0.1, joystick_button=5
        )(
            self.game.change_volume(0.05)
        )
        self.action('Save game', symbol=key.F3, joystick_button=7)(self.save)
        self.action(
            'Load game', symbol=key.F4, joystick_button=8
        )(self.world_context.load)
        return super().__attrs_post_init__()

    def build_inventory(self) -> None:
        """Build the player inventory.

        This method should be performed any time
        :attr:`~earwax.story.play_level.PlayLevel.state` changes.
        """
        obj: RoomObject
        while self.inventory:
            obj = self.inventory.pop()
            obj.location.objects[obj.id] = obj
        room: WorldRoom
        for room in list(self.world.rooms.values()):
            for obj in list(room.objects.values()):
                if obj.id in self.state.inventory_ids:
                    self.inventory.append(obj)
                    del room.objects[obj.id]

    def get_objects(self) -> List[RoomObject]:
        """Return a list of objects that the player can see.

        This method will exclude objects which are in the as yet unimplemented
        player inventory.
        """
        return [
            obj for obj in self.state.room.objects.values()
            if obj not in self.inventory
        ]

    def pause(self) -> None:
        """Pause All the currently-playing room sounds."""
        a: Ambiance
        for a in self.ambiances:
            if a.sound is not None:
                a.sound.paused = not a.sound.paused
        t: Track
        for t in self.tracks:
            if t.sound is not None:
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

    @property
    def object(self) -> Optional[ObjectTypes]:
        """Return the object from ``self.state``."""
        room: WorldRoom = self.state.room
        category: WorldStateCategories = self.state.category
        if category is WorldStateCategories.room:
            return room
        elif category is WorldStateCategories.objects:
            if self.state.object_index is not None:
                obj: RoomObject = self.get_objects()[self.state.object_index]
                return obj
        else:
            assert category is WorldStateCategories.exits
            if self.state.object_index is not None:
                x: RoomExit = room.exits[self.state.object_index]
                return x
        return None

    def stop_action_sounds(self) -> None:
        """Stop all action sounds."""
        while self.action_sounds:
            s: Sound = self.action_sounds.pop()
            s.destroy()

    def on_push(self) -> None:
        """Set the initial room.

        The room is the world from the :attr:`state` object, rather than the
        :attr:`~StoryWorld.initial_room`.
        """
        super().on_push()
        self.set_room(self.state.room)

    def on_pop(self) -> None:
        """Stop all the action sounds."""
        self.stop_action_sounds()
        return super().on_pop()

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
        if self.cursor_sound is not None:
            self.cursor_sound.destroy()
            self.cursor_sound = None
        data: List[str]
        room: WorldRoom = self.state.room
        category: WorldStateCategories = self.state.category
        if category is WorldStateCategories.room:
            data = [room.get_name(), room.get_description()]
        elif category is WorldStateCategories.objects:
            data = [o.name for o in self.get_objects()]
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
            position: Optional[Point] = None
            index: int
            if self.state.object_index is None:
                index = 0
            else:
                index = max(0, self.state.object_index + direction)
            if index >= len(data):
                index = len(data) - 1
            self.state.object_index = index
            self.game.output(data[self.state.object_index])
            if category is WorldStateCategories.objects:
                position = self.get_objects()[self.state.object_index].position
            elif category is WorldStateCategories.exits:
                position = room.exits[self.state.object_index].position
            self.play_cursor_sound(position)

    def use_exit(self, x: RoomExit) -> None:
        """Use the given exit.

        This method is called by the :meth:`activate` method.

        :param x: The exit to use.
        """
        a: WorldAction = x.action
        if a.message is not None:
            self.game.output(a.message)
        if a.sound is not None:
            self.game.interface_sound_manager.play_path(Path(a.sound), True)
        self.set_room(x.destination)

    def get_gain(self, type: TrackTypes, multiplier: float) -> float:
        """Return the proper gain."""
        start: float
        if type is TrackTypes.music:
            start = self.game.config.sound.music_volume.value
        else:
            start = self.game.config.sound.ambiance_volume.value
        return start * multiplier

    def set_room(self, room: WorldRoom) -> None:
        """Move to a new room."""
        assert self.game.ambiance_sound_manager is not None
        self.state.room_id = room.id
        self.state.object_index = None
        self.state.category_index = 0
        self.stop_action_sounds()
        self.stop_ambiances()
        self.ambiances.clear()
        ambiances: Dict[str, WorldAmbiance] = {
            a.path: a for a in room.ambiances
        }
        loaded_paths: List[str] = []
        track: Track
        for track in self.tracks.copy():
            if track.path not in ambiances:
                self.tracks.remove(track)
                track.stop()
            else:
                assert track.sound is not None
                track.sound.set_gain(
                    self.get_gain(
                        track.track_type,
                        ambiances[track.path].volume_multiplier
                    )
                )
                loaded_paths.append(track.path)
        a: WorldAmbiance
        for a in room.ambiances:
            if a.path not in loaded_paths:
                track = Track('file', a.path, TrackTypes.ambiance)
                track.play(self.game.ambiance_sound_manager)
                assert track.sound is not None
                track.sound.set_gain(
                    self.get_gain(
                        track.track_type, a.volume_multiplier
                    )
                )
                self.tracks.append(track)
        obj: RoomObject
        for obj in room.objects.values():
            for a in obj.ambiances:
                if obj.position is None:
                    track = Track('file', a.path, TrackTypes.ambiance)
                    self.tracks.append(track)
                    track.play(self.game.ambiance_sound_manager)
                else:
                    ambiance: Ambiance = Ambiance('file', a.path, obj.position)
                    self.ambiances.append(ambiance)
        self.start_ambiances()

    def do_action(
        self, action: WorldAction, obj: Union[RoomObject, RoomExit],
        pan: bool = True
    ) -> None:
        """Actually perform an action.

        :param action: The action to perform.

        :param obj: The object that owns this action.

            If this value is of type :class:`~earwax.story.world.RoomObject`,
            and its :attr:`~earwax.story.world.RoomObject.position` value is
            not ``None``, then the action sound will be panned accordingly..

        :param pan: If this value evaluates to ``False``, then regardless of
            the ``obj`` value, no panning will be performed.
        """
        if action.message is not None:
            name: str
            if isinstance(obj, RoomObject):
                name = obj.name
            else:
                name = action.name
            self.game.output(action.message.format(name))
        if action.sound is not None:
            position: Optional[Point] = None
            if isinstance(obj, RoomObject) and pan:
                position = obj.position
            self.play_action_sound(action.sound, position=position)

    def play_cursor_sound(self, position: Optional[Point]) -> None:
        """Play and set the cursor sound."""
        if self.world.cursor_sound is None:
            return

        self.cursor_sound = self.game.interface_sound_manager.play_path(
            Path(self.world.cursor_sound), False, position=position
        )

    def play_action_sound(
        self, sound: str, position: Optional[Point] = None
    ) -> None:
        """Play an action sound.

        :param sound: The filename of the sound to play.

        :param position: The position of the owning object.

            If this value is ``None``, the sound will not be panned.
        """
        s: Sound = self.game.interface_sound_manager.play_path(
            Path(sound), True, position=position
        )
        self.action_sounds.append(s)

    def perform_action(self, obj: RoomObject, action: WorldAction) -> Callable[
        [], None
    ]:
        """Return a function that will perform an object action.

        This method is used by :meth:`actions_menu` to allow the player to
        trigger object actions.

        The inner method performs the following actions:

        * Shows the action message to the player.

        * Plays the action sound. If ``obj`` has coordinates, the sound will be
            heard at those coordinates.

        * Pops the level to remove the actions menu from the stack.

        :param obj: The object which has the action.

        :param action: The action which should be performed.
        """

        def inner() -> None:
            """Actually perform the action."""
            if action is obj.take_action or action is self.world.take_action:
                self.take_object(obj)
            elif action is obj.drop_action or action is self.world.drop_action:
                self.drop_object(obj)()
            else:
                self.do_action(action, obj)
                self.game.pop_level()

        return inner

    def actions_menu(
        self, obj: RoomObject, menu_action: Optional[WorldAction] = None
    ) -> None:
        """Show a menu of object actions."""
        actions: List[WorldAction] = obj.actions.copy()
        action: WorldAction
        if obj.is_takeable and obj not in self.inventory:
            if obj.take_action is None:
                action = self.world.take_action
            else:
                action = obj.take_action
            actions.append(action)
        if obj.is_droppable and obj in self.inventory:
            if obj.drop_action is None:
                action = self.world.drop_action
            else:
                action = obj.drop_action
            actions.append(action)
        if not actions:
            return self.game.output(self.world.messages.no_actions)
        msg: str
        sound: Optional[str] = None
        if menu_action is None:
            if (
                obj.actions_action is not None and
                obj.actions_action.message is not None
            ):
                msg = obj.actions_action.message
            else:
                msg = self.world.messages.actions_menu
            if obj.take_action is None:
                sound = self.world.take_action.sound
            else:
                sound = obj.take_action.sound
        else:
            sound = menu_action.sound
            if menu_action.message is None:
                msg = msg = self.world.messages.actions_menu
            else:
                msg = menu_action.message
        m: Menu = Menu(self.game, msg.format(obj.name))
        if sound is not None:
            self.play_action_sound(sound)
        for action in actions:
            m.add_item(
                self.perform_action(obj, action),
                title=action.name.format(obj.name)
            )
        self.game.push_level(m)

    def activate(self) -> None:
        """Activate the currently focussed object."""
        if self.state.object_index is None:
            self.state.object_index = 0
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
                obj: RoomObject = self.get_objects()[self.state.object_index]
                self.actions_menu(obj)
            else:
                self.game.output(self.world.messages.no_objects)

    def save(self) -> None:
        """Save the current state."""
        directory: Path = self.game.get_settings_path()
        if not directory.is_dir():
            try:
                directory.mkdir()
                self.world_context.logger.info(
                    'Created game settings directory %s.',
                    self.game.get_settings_path()
                )
            except Exception as e:
                self.game.output(
                    'Unable to create game settings directory: %s' % e
                )
                return self.world_context.logger.exception(
                    'Failed to create game settings directory.'
                )
        data: Dict[str, Any] = self.state.dump()
        try:
            self.world_context.logger.info('Saving game state: %r.', data)
            with self.world_context.config_file.open('w') as f:
                f.write(dump(data, Dumper=CDumper))
            self.game.output('Game saved.')
        except Exception as e:
            self.game.output('Unable to create save file: %s' % e)
            self.world_context.logger.exception('Failed to create save file.')

    def object_menu(self, obj: RoomObject) -> Callable[[], None]:
        """Return a callable which shows the inventory menu for an object."""

        def inner() -> None:
            m: Menu = Menu(self.game, title=obj.name)
            if obj.use_action is not None:
                m.add_item(
                    self.use_object(obj),
                    title=obj.use_action.name.format(obj.name)
                )
            if obj.is_droppable:
                action: WorldAction
                if obj.drop_action is None:
                    action = self.world.drop_action
                else:
                    action = obj.drop_action
                m.add_item(
                    self.drop_object(obj), title=action.name.format(obj.name)
                )
            if obj.is_droppable or obj.is_usable:
                self.game.push_level(m)

        return inner

    def inventory_menu(self) -> None:
        """Show the inventory menu."""
        if not self.inventory:
            return self.game.output(self.world.messages.empty_inventory)
        m: Menu = Menu(self.game, self.world.messages.inventory_menu)
        obj: RoomObject
        for obj in self.inventory:
            m.add_item(self.object_menu(obj), title=obj.name)
        self.game.push_level(m)

    def take_object(self, obj: RoomObject) -> None:
        """Take an object."""
        action: WorldAction
        if obj.take_action is None:
            action = self.world.take_action
        else:
            action = obj.take_action
        self.do_action(action, obj)
        self.inventory.append(obj)
        del obj.location.objects[obj.id]
        self.state.inventory_ids.append(obj.id)
        self.game.reveal_level(self)

    def drop_object(self, obj: RoomObject) -> Callable[[], None]:
        """Return a callable that can be used to drop an object."""

        def inner() -> None:
            self.game.reveal_level(self)
            action: WorldAction
            if obj.drop_action is None:
                action = self.world.drop_action
            else:
                action = obj.drop_action
            self.do_action(action, obj, pan=False)
            self.state.room.objects[obj.id] = obj
            self.state.inventory_ids.remove(obj.id)
            self.inventory.remove(obj)

        return inner

    def use_object(self, obj: RoomObject) -> Callable[[], None]:
        """Return a callable that can be used to use an object."""

        def inner() -> None:
            self.game.reveal_level(self)
            return self.actions_menu(obj, menu_action=obj.use_action)

        return inner

    def objects_menu(
        self, objects: List[RoomObject],
        func: Callable[[RoomObject], Callable[[], None]],
        title: str
    ) -> None:
        """Push a menu of objects."""
        m: Menu = Menu(self.game, title)
        obj: RoomObject
        for obj in objects:
            m.add_item(func(obj), title=obj.name)
        self.game.push_level(m)

    def drop_object_menu(self) -> None:
        """Push a menu that can be used to drop an object."""
        objects: List[RoomObject] = [
            x for x in self.inventory if x.is_droppable
        ]
        if objects:
            self.objects_menu(objects, self.drop_object, 'Drop Object')
        else:
            self.game.output(self.world.messages.nothing_to_drop)

    def use_object_menu(self) -> None:
        """Push a menu that allows using an object."""
        objects: List[RoomObject] = [x for x in self.inventory if x.is_usable]
        if objects:
            self.objects_menu(objects, self.use_object, 'Use Object')
        else:
            self.game.output(self.world.messages.nothing_to_use)

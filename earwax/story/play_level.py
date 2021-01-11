"""Provides the StoryLevel class."""

from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List,
                    Optional)

from attr import Factory, attrib, attrs
from yaml import dump

try:
    from yaml import CDumper
except ImportError:
    from yaml import Dumper as CDumper  # type: ignore[misc]

from ..ambiance import Ambiance
from ..level import Level
from ..menu import Menu
from ..point import Point
from ..sound import Sound
from ..track import Track, TrackTypes
from .world import (RoomExit, RoomObject, StoryWorld, WorldAction,
                    WorldAmbiance, WorldRoom, WorldState, WorldStateCategories)

try:
    from pyglet.window import key
    from synthizer import DirectSource, Source, Source3D
except ModuleNotFoundError:
    key = None
    DirectSource, Source, Source3D = (object, object, object)


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
        self.action('Volume down', symbol=key.PAGEDOWN, interval=0.1)(
            self.game.change_volume(-0.05)
        )
        self.action('Volume Up', symbol=key.PAGEUP, interval=0.1)(
            self.game.change_volume(0.05)
        )
        self.action('Save game', symbol=key.F3)(self.save)
        self.action('Load game', symbol=key.F4)(self.world_context.load)
        return super().__attrs_post_init__()

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

    def stop_action_sounds(self) -> None:
        """Stop all action sounds."""
        while self.action_sounds:
            s: Sound = self.action_sounds.pop()
            s.destroy(destroy_source=True)

    def on_push(self) -> None:
        """Set the initial room.

        When game saving is implemented, this will be the world from the
        :attr:`state` object, rather than the :attr:`~StoryWorld.initial_room`.
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
            self.cursor_sound.destroy(destroy_source=True)
            self.cursor_sound = None
        data: List[str]
        room: WorldRoom = self.state.room
        category: WorldStateCategories = self.state.category
        if category is WorldStateCategories.room:
            data = [room.get_name(), room.get_description()]
        elif category is WorldStateCategories.objects:
            data = [o.name for o in room.get_objects()]
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
                position = room.get_objects()[self.state.object_index].position
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

    def set_room(self, room: WorldRoom) -> None:
        """Move to a new room."""
        assert self.game.ambiance_sound_manager is not None
        self.state.room_id = room.id
        self.state.object_index = None
        self.state.category_index = 0
        self.stop_action_sounds()
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
                track = Track('file', path_str, TrackTypes.ambiance)
                track.play(self.game.ambiance_sound_manager)
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
        self, action: WorldAction, position: Optional[Point] = None
    ) -> None:
        """Actually perform an action.

        :param action: The action to perform.

        :param position: The position of whatever object owns this action.

            If this value is ``None``, then ``action.sound`` will not be
            panned.
        """
        if action.message is not None:
            self.game.output(action.message)
        if action.sound is not None:
            self.play_action_sound(action.sound, position=position)

    def play_cursor_sound(self, position: Optional[Point]) -> None:
        """Play and set the cursor sound."""
        if self.world.cursor_sound is None:
            return
        source: Source
        if position is None:
            source = DirectSource(self.game.audio_context)
        else:
            source = Source3D(self.game.audio_context)
            source.gain = self.game.config.sound.sound_volume.value
            source.position = position.coordinates
        self.cursor_sound = Sound.from_path(
            self.game.audio_context, source, self.game.buffer_cache,
            Path(self.world.cursor_sound)
        )

    def play_action_sound(
        self, sound: str, position: Optional[Point] = None
    ) -> None:
        """Play an action sound.

        :param sound: The filename of the sound to play.

        :param position: The position of the owning object.

            If this value is ``None``, the sound will not be panned.
        """
        source: Source
        if position is None:
            source = DirectSource(self.game.audio_context)
        else:
            source = Source3D(self.game.audio_context)
            source.position = position.coordinates
        source.gain = self.game.config.sound.sound_volume.value
        s: Sound = Sound.from_path(
            self.game.audio_context, source, self.game.buffer_cache,
            Path(sound)
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
            self.do_action(action, position=obj.position)
            self.game.pop_level()

        return inner

    def actions_menu(self, obj: RoomObject) -> None:
        """Show a menu of object actions."""
        if not obj.actions:
            return self.game.output(self.world.messages.no_actions)
        msg: str
        if (
            obj.actions_action is not None and
            obj.actions_action.message is not None
        ):
            msg = obj.actions_action.message
        else:
            msg = self.world.messages.actions_menu
        m: Menu = Menu(self.game, msg.format(obj.name))
        if (
            obj.actions_action is not None and
            obj.actions_action.sound is not None
        ):
            self.play_action_sound(obj.actions_action.sound)
        action: WorldAction
        for action in obj.actions:
            m.add_item(self.perform_action(obj, action), title=action.name)
        self.game.push_level(m)

    def activate(self) -> None:
        """Activate the currently focussed object."""
        assert self.state.object_index is not None
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
                obj: RoomObject = room.get_objects()[self.state.object_index]
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

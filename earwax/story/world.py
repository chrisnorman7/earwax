"""Provides various classes relating to worlds."""

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from attr import Factory, attrib, attrs
from shortuuid import uuid

from ..credit import Credit
from ..mixins import DumpLoadMixin
from ..point import Point
from ..reverb import Reverb

if TYPE_CHECKING:
    from ..game import Game

ObjectTypes = Union['WorldRoom', 'RoomObject', 'RoomExit']


class StringMixin:
    """Provides an ``__str__`` method."""

    def __str__(self) -> str:
        """Return this object as a string."""
        assert isinstance(self, (WorldRoom, RoomObject))
        return f'{self.name} (#{self.id})'


class DumpablePoint(Point, DumpLoadMixin):
    """A point that can be dumped and loaded."""


class DumpableReverb(Reverb, DumpLoadMixin):
    """A reverb that can be dumped."""


@attrs(auto_attribs=True)
class WorldAmbiance(DumpLoadMixin):
    """An ambiance.

    This class represents a looping sound, which is either attached to a
    :class:`~WorldRoom` instance, or a :class:`~RoomObject` instance.

    :ivar ~earwax.story.WorldAmbiance.path: The path to a sound file.

    :ivar ~earwax.story.WorldAmbiance.volume_multiplier: A value to multiply
        the ambiance volume by to get the volume for this sound..
    """

    path: str
    volume_multiplier: float = 1.0

    def __str__(self) -> str:
        """Return a string."""
        return f'Ambiance {self.path}'


@attrs(auto_attribs=True)
class WorldAction(DumpLoadMixin):
    """An action that can be performed.

    Actions are used by the :class:`RoomObject` and :class:`RoomExit` classes.

    If attached to a :class:`~RoomObject` instance, its
    :attr:`~WorldAction.name` will appear in the :meth:`action menu
    <StoryWorld.actions_menu>`. If attached to a :class:`~RoomExit` instance,
    then its :attr:`~WorldAction.name` will appear in the exits list.

    :ivar ~earwax.story.WorldAction.name: The name of this action.

    :ivar ~earwax.story.WorldAction.message: The message that is shown to the
        player when this action is used.

        If this value is omitted, no message will be shown.

    :ivar ~earwax.story.WorldAction.sound: The sound that should play when this
        action is used.

        If this value is omitted, no sound will be heard.
    """

    name: str = 'Unnamed Action'
    message: Optional[str] = None
    sound: Optional[str] = None

    def __str__(self) -> str:
        """Return a string."""
        return self.name


class RoomObjectTypes(Enum):
    """The type of a room object.

    :ivar ~earwax.story.world.WorldObjectTypes.stuck: This object cannot be
        moved.

    :ivar ~earwax.story.world.WorldObjectTypes.takeable: This object can be
        picked up.

    :ivar ~earwax.story.world.WorldObjectTypes.droppable: This object can be
        dropped.

        This value automatically implies
        :attr:`~earwax.story.world.WorldObjectTypes.takeable`.
    """

    stuck = 0
    takeable = 1
    droppable = 2
    usable: int = 4


@attrs(auto_attribs=True)
class RoomObject(StringMixin, DumpLoadMixin):
    """An object in the story.

    Instances of this class will either sit in a room, or be in the player's
    inventory.

    :ivar ~earwax.story.RoomObject.id: The unique ID of this object. If this ID
        is not provided, then picking it up will not be reliable, as the ID
        will be randomly generated.

        Other than the above restriction, you can set the ID to be whatever you
        like.

    :ivar ~earwax.story.RoomObject.location: The room where this object is
        located.

        This value is set by the :meth:`~earwax.story.world.StoryWorld` which
        holds this instance.

        If this object is picked up, the location will not change, but this
        object will be removed from the location's
        :attr:`~earwax.story.world.WorldRoom.objects` dictionary.

    :ivar ~earwax.story.RoomObject.name: The name of this object.

        This value will be used in any list of objects.

    :ivar ~earwax.story.RoomObject.actions_action: An action object which will
        be used when viewing the actions menu for this object.

        If this value is ``None``, no music will play when viewing the actions
        menu for this object, and the
        :attr:`~earwax.story.WorldMessages.actions_menu` message will be shown.

    :ivar ~earwax.story.RoomObject.ambiances: A list of ambiances to play at
        the :attr:`~earwax.story.RoomObject.position` of this object.

    :ivar ~earwax.story.RoomObject.actions: A list of actions that can be
        performed on this object.

    :ivar ~earwax.story.world.RoomObject.position: The position of this object.

        If this value is ``None``, then any :attr:`ambiances` will not be
        panned.

    :ivar ~earwax.story.world.RoomObject.drop_action: The action that will be
        used when this object is dropped by the player.

        If this value is ``None``, the containing world's
        :attr:`~earwax.story.world.StoryWorld.drop_action` attribute will be
        used.

    :ivar ~earwax.story.world.RoomObject.take_action: The action that will be
        used when this object is taken by the player.

        If this value is ``None``, the containing world's
        :attr:`~earwax.story.world.StoryWorld.take_action` attribute will be
        used.

    :ivar ~earwax.story.world.RoomObject.use_action: The action that will be
        used when this object is used by the player.

        If this value is ``None``, then this object is considered unusable.

    :ivar ~earwax.story.world.RoomObject.type: Specifies what sort of object
        this is.
    """

    id: str = Factory(uuid)
    name: str = 'Unnamed Object'
    actions_action: Optional[WorldAction] = None
    ambiances: List[WorldAmbiance] = Factory(list)
    actions: List[WorldAction] = Factory(list)
    position: Optional[DumpablePoint] = None
    drop_action: Optional[WorldAction] = None
    take_action: Optional[WorldAction] = None
    use_action: Optional[WorldAction] = None
    type: RoomObjectTypes = Factory(lambda: RoomObjectTypes.stuck)
    location: 'WorldRoom' = attrib(init=False, repr=False)

    __excluded_attribute_names__ = ['location']

    @property
    def is_stuck(self) -> bool:
        """Return ``True`` if this object is stuck."""
        return self.type is RoomObjectTypes.stuck

    @property
    def is_takeable(self) -> bool:
        """Return ``True`` if this object can be taken."""
        return (
            self.type is RoomObjectTypes.takeable
            or self.type is RoomObjectTypes.droppable
        )

    @property
    def is_droppable(self) -> bool:
        """Return ``True`` if this object can be dropped."""
        return self.type is RoomObjectTypes.droppable

    @property
    def is_usable(self) -> bool:
        """Return ``True`` if this object can be used."""
        return self.use_action is not None


@attrs(auto_attribs=True)
class RoomExit(DumpLoadMixin):
    """An exit between two rooms.

    Instances of this class rely on their :attr:`action` property to show
    messages and play sounds, as well as for the name of the exit.

    The actual destination can be retrieved with the :attr:`destination`
    property.

    :ivar ~earwax.story.world.RoomExit.destination_id: The ID of the room on
        the other side of this exit.

    :ivar ~earwax.story.RoomExit.location: The location of this exit.

        This value is provided by the containing
        :class:`~earwax.story.world.StoryWorld` class.

    :ivar ~earwax.story.RoomExit.action: An action to perform when using this
        exit.

    :ivar ~earwax.story.world.RoomExit.position: The position of this exit.

        If this value is ``None``, then any :attr:`ambiances` will not be
        panned.
    """

    destination_id: str
    action: WorldAction = attrib(Factory(WorldAction), repr=False)
    position: Optional[DumpablePoint] = None
    location: 'WorldRoom' = attrib(init=False)

    __excluded_attribute_names__ = ['location']

    @property
    def destination(self) -> 'WorldRoom':
        """Return the room this exit leads from.

        This value is inferred from :attr:`destination_id`.
        """
        return self.location.world.rooms[self.destination_id]

    def __str__(self) -> str:
        """Return a string."""
        return (
            f'{self.action.name} ({self.location.get_name()} -> '
            f'{self.destination.get_name()})'
        )


@attrs(auto_attribs=True)
class WorldRoom(DumpLoadMixin, StringMixin):
    """A room in a world.

    Rooms can contain exits and object.

    It is worth noting that both the room :attr:`name` and :attr:`description`
    can either be straight text, or they can consist of a hash character (#)
    followed by the ID of another room, from which the relevant attribute will
    be presented at runtime.

    If this is the case, changing the name or description of the referenced
    room will change the corresponding attribute on the first instance.

    This convertion can only happen once, as otherwise there is a risk of
    circular dependencies, causing a ``RecursionError`` to be raised.

    :ivar ~earwax.story.WorldRoom.world: The world this room is part of.

        This value is set by the containing
        :class:`~earwax.story.world.StoryRoom` instance.

    :ivar ~earwax.story.WorldRoom.id: The unique ID of this room.

        If this value is not provided, then an ID will be generated, based on
        the number of rooms that have already been loaded.

        If you want to link this room with exits, it is *highly* recommended
        that you provide your own ID.

    :ivar ~earwax.story.WorldRoom.name: The name of this room, or the #id of a
        room to inherit the name from.

    :ivar ~earwax.story.WorldRoom.description: The description of this room, or
        the #id of another room to inherit the description from.

    :ivar ~earwax.story.WorldRoom.ambiances: A list of ambiances to play when
        this room is in focus.

    :ivar ~earwax.story.WorldRoom.objects: A mapping of object ids to objects.

        To get a list of objects, the canonical way is to use the
        :meth:`earwax.story.play_level.PlayLevel.get_objects` method, as this
        will properly hide objects which are in the player's inventory.

    :ivar ~earwax.story.WorldRoom.exits: A list of exits from this room.
    """

    id: str = Factory(uuid)
    name: str = 'Unnamed Room'
    description: str = 'Not described.'
    ambiances: List[WorldAmbiance] = Factory(list)
    objects: Dict[str, RoomObject] = Factory(dict)
    exits: List[RoomExit] = Factory(list)
    reverb: Optional[DumpableReverb] = None
    world: 'StoryWorld' = attrib(init=False, repr=False)

    __excluded_attribute_names__ = ['world']

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

    def create_exit(self, destination: 'WorldRoom', **kwargs) -> RoomExit:
        """Create and return an exit that links this room to another.

        This method will add the new exits to this room's
        :attr:`~earwax.story.world.WorldRoom.exits` list, and set the
        appropriate :attr:`~earwax.story.world.RoomExit.location` on the new
        exit.

        :param destination: The destination whose ID will become the new exit's
            :attr:`~earwax.story.world.RoomExit.destination_id`.

        :param kwargs: Extra keyword arguments to pass to the
            :class:`~earwax.story.world.RoomExit` constructor..
        """
        x: RoomExit = RoomExit(destination.id, **kwargs)
        x.location = self
        self.exits.append(x)
        return x

    def create_object(self, **kwargs) -> RoomObject:
        """Create and return an exit from the provided ``kwargs``.

        This method will add the created object to this room's
        :attr:`~earwax.story.world.WorldRoom.objects` dictionary, and set the
        appropriate :attr:`~earwax.story.world.RoomObject.location` attribute.

        :param kwargs: Keyword arguments to pass to the constructor of
            :class:`~earwax.story.world.RoomObject`.
        """
        obj: RoomObject = RoomObject(**kwargs)
        obj.location = self
        self.objects[obj.id] = obj
        return obj


@attrs(auto_attribs=True)
class WorldMessages(DumpLoadMixin):
    """All the messages that can be shown to the player.

    When adding a message to this class, make sure to add the same message and
    an appropriate description to the ``message_descriptions`` in
    ``earwax/story/edit_level.py``.

    :ivar ~earwax.story.WorldMessages.no_objects: The message which is shown
        when the player cycles to an empty list of objects.

    :ivar ~earwax.story.WorldMessages.no_actions: The message which is shown
        when there are no actions for an object.

    :ivar ~earwax.story.WorldMessages.no_exits: The message which is shown when
            the player cycles to an empty list of exits.

    :ivar ~earwax.story.WorldMessages.no_use: The message which is shown when
        the player tries to use an object which cannot be used.

    :ivar ~earwax.story.WorldMessages.nothing_to_use: The message which is
        shown when accessing the use menu with no usable objects.

    :ivar ~earwax.story.WorldMessages.nothing_to_drop: The message which is
        shown when accessing the drop menu with no droppable items.

    :ivar ~earwax.story.WorldMessages.empty_inventory: The message which is
        shown when trying to access an empty inventory menu.

    :ivar ~earwax.story.WorldMessages.room_activate: The message which is shown
        when enter is pressed with the room category selected.

        Maybe an action attribute should be added to rooms, so that enter can
        be used everywhere?

    :ivar ~earwax.story.WorldMessages.room_category: The name of the "room"
        category.

    :ivar ~earwax.story.WorldMessages.objects_category: The name of the
        "objects" category.

    :ivar ~earwax.story.WorldMessages.exits_category: The name of the "exits"
        category.

    :ivar ~earwax.story.WorldMessages.actions_menu: The message which is shown
        when the actions menu is activated.

    :ivar ~earwax.story.WorldMessages.inventory_menu: The title of the
        inventory menu.

        You can include the name of the object in question, by including a set
        of braces::

            <message id="actions_menu">You examine {}.</message>

    :ivar ~earwax.story.WorldMessages.main_menu: The title of the main menu.

    :ivar ~earwax.story.WorldMessages.play_game: The title of the "play game"
        entry in the main menu.

    :ivar ~earwax.story.WorldMessages.load_game: The title of the "load game"
        entry in the main menu.

    :ivar ~earwax.story.WorldMessages.show_credits: The title of the "show
        credits" entry in the main menu.

    :ivar ~earwax.story.WorldMessages.credits_menu: The title of the credits
        menu.

    :ivar ~earwax.story.WorldMessages.welcome: The message which is shown when
        play starts.

    :ivar ~earwax.story.WorldMessages.no_saved_game: The message which is
        spoken when there is no game to load.

    :ivar ~earwax.story.WorldMessages.exit: The title of the "exit" entry of
        the main menu.
    """

    # Empty category and failure messages:
    no_objects: str = 'This room is empty.'
    no_actions: str = 'There is nothing you can do with this object.'
    no_exits: str = 'There is no way out of this room.'
    no_use: str = 'You cannot use {}.'
    nothing_to_use: str = 'You have nothing that can be used.'
    nothing_to_drop: str = 'You have nothing that can be dropped.'
    empty_inventory: str = "You aren't carrying anything."
    room_activate: str = 'You cannot do that.'

    # Category names:
    room_category: str = 'Location'
    objects_category: str = 'Objects'
    exits_category: str = 'Exits'

    # Menu messages:
    actions_menu: str = 'You step up to {}.'
    inventory_menu: str = 'Inventory'
    main_menu: str = 'Main Menu'
    play_game: str = 'Start new game'
    load_game: str = 'Load game'
    show_credits: str = 'Show Credits'
    credits_menu: str = 'Credits'
    welcome: str = 'Welcome to this game.'
    no_saved_game: str = 'You have no game saved.'
    exit: str = 'Exit'

    def __str__(self) -> str:
        """Return a string."""
        return 'World messages'


@attrs(auto_attribs=True)
class StoryWorld(DumpLoadMixin):
    """The top level world object.

    Worlds can contain rooms and messages, as well as various pieces of
    information about themselves.

    :ivar ~earwax.story.StoryWorld.game: The game this world is part of.

    :ivar ~earwax.story.StoryWorld.name: The name of this world.

    :ivar ~earwax.story.StoryWorld.author: The author of this world.

        The format of this value is arbitrary, although
        ``Author Name <author@domain.com>`` is recommended.

    :ivar ~earwax.story.StoryWorld.main_menu_musics: A list of filenames to
        play as music while the main menu is being shown.

    :ivar ~earwax.story.StoryWorld.cursor_sound: The sound that will play when
        moving over objects.

        If this value is ``None``, no sound will be heard.

    :ivar ~earwax.story.StoryWorld.rooms: A mapping of room IDs to rooms.

    :ivar ~earwax.story.StoryWorld.initial_room_id: The ID of the room to be
        used when first starting the game.

    :ivar ~earwax.story.StoryWorld.messages: The messages object used by this
        world.
    """

    game: 'Game'
    name: str = 'Untitled World'
    author: str = 'Unknown'

    main_menu_musics: List[str] = Factory(list)
    cursor_sound: Optional[str] = None
    empty_category_sound: Optional[str] = None
    rooms: Dict[str, WorldRoom] = Factory(dict)
    initial_room_id: Optional[str] = None
    messages: WorldMessages = Factory(WorldMessages)
    take_action: WorldAction = Factory(
        lambda: WorldAction(name='Take', message='You take {}.')
    )
    drop_action: WorldAction = Factory(
        lambda: WorldAction(name='Drop', message='You drop {}.')
    )
    panner_strategy: str = Factory(lambda: 'best')

    __excluded_attribute_names__ = ['game']

    def __attrs_post_init__(self) -> None:
        """Set all the location attributes."""
        room: WorldRoom
        for room in self.rooms.values():
            room.world = self
            obj: RoomObject
            for obj in room.objects.values():
                obj.location = room
            x: RoomExit
            for x in room.exits:
                x.location = room

    @classmethod
    def load(cls, data: Dict[str, Any], *args) -> Any:
        """Load credits before anything else."""
        world: StoryWorld = super().load(data, *args)
        config_data: Dict[str, Any] = data.get('config', None)
        if config_data is not None:
            world.game.config.populate_from_dict(config_data)
        credit_data: Dict[str, Any]
        for credit_data in data.get('credits', []):
            path: Optional[Path] = None
            p: Optional[str] = credit_data.get('sound', None)
            if p is not None:
                path = Path(p)
            world.game.credits.append(
                Credit(
                    credit_data['name'], credit_data['url'], sound=path,
                    loop=credit_data.get('loo', True)
                )
            )
        return world

    @property
    def initial_room(self) -> Optional[WorldRoom]:
        """Return the initial room for this world."""
        if self.initial_room_id is not None:
            return self.rooms[self.initial_room_id]
        return None

    def add_room(
        self, room: WorldRoom, initial: Optional[bool] = None
    ) -> None:
        """Add a room to this world.

        :param room: The room to add.

        :param initial: An optional boolean to specify whether the given room
            should become the
            :attr:`~earwax.story.world.StoryWorld.initial_room` or not.

            If this value is ``None``, then this room will be set as default if
            :attr:`~earwax.story.world.StoryWorld.initial_room_id` is itself
            ``None``.
        """
        self.rooms[room.id] = room
        room.world = self
        if initial or (initial is None and self.initial_room_id is None):
            self.initial_room_id = room.id

    def __str__(self) -> str:
        """Return a string."""
        return f'World({self.name!r})'

    def dump(self) -> Dict[str, Any]:
        """Dump this world."""
        data: Dict[str, Any] = super().dump()
        data['config'] = self.game.config.dump()
        credits_list: List[Dict[str, Any]] = []
        credit: Credit
        for credit in self.game.credits:
            credits_list.append(
                {
                    'name': credit.name,
                    'url': credit.url,
                    'sound': None
                    if credit.sound is None else str(credit.sound),
                    'loop': credit.loop
                }
            )
        data['credits'] = credits_list
        return data


class WorldStateCategories(Enum):
    """The various categories the player can select.

    :ivar ~earwax.story.WorldStateCategories.room: The category where the name
        and description of a room are shown.

    :ivar ~earwax.story.WorldStateCategories.objects: The category where the
        objects of a room are shown.

    :ivar ~earwax.story.WorldStateCategories.exits: The category where the
        exits of a room are shown.
    """

    room = 0
    objects = 1
    exits = 2


@attrs(auto_attribs=True)
class WorldState(DumpLoadMixin):
    """The state of a story.

    With the exception of the :attr:`world` attribute, this class should only
    have primitive types as its attributes, so that instances can be easily
    dumped to yaml.

    :ivar ~earwax.story.WorldState.world: The world this state represents.

    :ivar ~earwax.story.WorldState.room_id: The ID of the current room.

    :ivar ~earwax.story.WorldState.inventory_ids: A list of object IDs which
        make up the player's inventory.

    :ivar ~earwax.story.WorldState.category_index: The player's position in the
        list of categories.

    :ivar ~earwax.story.WorldState.object_index: The player's position in the
        current category.
    """

    world: StoryWorld

    room_id: str = attrib()

    @room_id.default
    def get_default_room_id(instance: 'WorldState') -> str:
        """Get the first room ID from the attached world.

        :param instance: The instance to work on.
        """
        assert instance.world.initial_room_id is not None
        return instance.world.initial_room_id

    inventory_ids: List[str] = Factory(list)
    category_index: int = Factory(int)
    object_index: Optional[int] = None

    __excluded_attribute_names__ = ['world']

    @property
    def room(self) -> WorldRoom:
        """Get the current room."""
        return self.world.rooms[self.room_id]

    @property
    def category(self) -> WorldStateCategories:
        """Return the current category."""
        return list(WorldStateCategories)[self.category_index]

"""Provides various classes relating to worlds."""

from enum import Enum
from typing import Dict, List, Optional, Type, Union
from xml.dom.minidom import Document, parseString
from xml.etree.ElementTree import Element, tostring

from attr import Factory, attrib, attrs

from ..point import Point
from .util import get_element, stringify

ObjectTypes = Union['WorldRoom', 'RoomObject', 'RoomExit']


@attrs(auto_attribs=True)
class WorldAmbiance:
    """An ambiance.

    This class represents a looping sound, which is either attached to a
    :class:`~WorldRoom` instance, or a :class:`~RoomObject` instance.

    Instances are created with the ``<ambiance>`` tag::

        <ambiance>Loop.wav</ambiance>

    :ivar ~earwax.story.WorldAmbiance.path: The path to a sound file.
    """

    path: str

    def to_xml(self) -> Element:
        """Dump this ambiance."""
        return get_element('ambiance', text=self.path)

    def __str__(self) -> str:
        """Return a string."""
        return f'Ambiance {self.path}'


@attrs(auto_attribs=True)
class WorldAction:
    """An action that can be performed.

    Actions are used by the :class:`RoomObject` and :class:`RoomExit` classes.

    If attached to a :class:`~RoomObject` instance, its
    :attr:`~WorldAction.name` will appear in the :meth:`action menu
    <StoryWorld.actions_menu>`. If attached to a :class:`~RoomExit` instance,
    then its :attr:`~WorldAction.name` will appear in the exits list.

    Instances are created with the ``<action>`` tag::

        <action>
            <name>Action name</name>
            <sound>sound.wav</sound>
            <message>The message shown when this action is performed.</message>
        </action>

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

    def to_xml(self) -> Element:
        """Dump this object."""
        e: Element = get_element('action')
        e.append(get_element('name', text=self.name))
        if self.message is not None:
            e.append(get_element('message', text=self.message))
        if self.sound is not None:
            e.append(get_element('sound', text=self.sound))
        return e

    def __str__(self) -> str:
        """Return a string."""
        return self.name


@attrs(auto_attribs=True)
class RoomObject:
    """An object in the story.

    Instances of this class will either sit in a room, or be in the player's
    inventory.

    You can create instances of this class with the ``<object>`` tag::

        <object x="-2" y="2" z="0">
            <name>Object Name</name>
            <ambiance>sound.wav</ambiance>
            <action>...</action>
        </object>

    :ivar ~earwax.story.RoomObject.id: The unique ID of this object. If this ID
        is not provided, then picking it up will not be reliable, as the ID
        will be randomly generated.

        Other than the above restriction, you can set the ID to be whatever you
        like.

    :ivar ~earwax.story.RoomObject.location: The room where this object is
        located.

        You do not set this attribute in XML, as it is inferred from which room
        holds the ``<object>`` tag.

        If this object is picked up, the location will not change, it will just
        not show up in the objects list.

    :ivar ~earwax.story.RoomObject.position: The position of this object.

        This value is provided in XML with the ``x``, ``y``, and ``z``
        attributes.

        If this value is ``None``, then any :attr:`ambiances` will not be
        panned.

    :ivar ~earwax.story.RoomObject.name: The name of this object.

        You can provide this value in XML, with a ``<name>`` tag.

    :ivar ~earwax.story.RoomObject.ambiances: A list of ambiances to play at
        the :attr:`~earwax.story.RoomObject.position` of this object.

    :ivar ~earwax.story.RoomObject.actions: A list of actions that can be
        performed on this object.
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

    def __str__(self) -> str:
        """Return a string."""
        return stringify(self)


@attrs(auto_attribs=True)
class RoomExit:
    """An exit between two rooms.

    Instances of this class rely on their :attr:`action` property to show
    messages and play sounds, as well as for the name of the exit.

    Instances of this class are created with the ``<exit>`` tag::

        <exit destination="jungle_2">
            <action>...</action>
        </exit>

    The ``destination`` attribute will be converted to :attr:`destination_id`.

    The actual destination can be retrieved with the :attr:`destination`
    property.

    :ivar ~earwax.story.RoomExit.location: The location of this exit.

        You cannot set this in XML, as it is inferred from the room which
        contains the ``<exit>`` tag.

    :ivar ~earwax.story.RoomExit.destination_id: The ID of the room on the
        other side of this exit.

        You provide this in XML with the ``destination`` attribute.

        *note*: The XML attribute is not called ``id``, as it might become
        possible to give exits IDs in the future so that extra code can be
        placed upon them.

    :ivar ~earwax.story.RoomExit.action: An action to perform when using this
        exit.
    """

    location: 'WorldRoom'
    destination_id: str
    action: WorldAction = Factory(WorldAction)

    @property
    def destination(self) -> 'WorldRoom':
        """Return the room this exit leads from.

        This value is inferred from :attr:`destination_id`.
        """
        return self.location.world.rooms[self.destination_id]

    def to_xml(self) -> Element:
        """Dump this exit."""
        e: Element = get_element(
            'exit', attrib={'destination': self.destination_id}
        )
        e.append(self.action.to_xml())
        return e
        return e

    def __str__(self) -> str:
        """Return a string."""
        return self.action.name or 'Unnamed Exit'


@attrs(auto_attribs=True)
class WorldRoom:
    """A room in a world.

    Rooms can contain exits and object.

    You can create instances of this class with the ``<room>`` tag::

        <room id="jungle_2">
            <name>Room Name (or #room_id)</name>
            <description>Room description (or #room_id).</description>
            <ambiance>Loop.wav</ambiance>
            <exit>...</exit>
            <object>...</object>
        </room>

    It is worth noting that both the room :attr:`name` and :attr:`description`
    can either be straight text, or they can consist of a hash character (#)
    followed by the ID of another room, from which the relevant attribute will
    be presented at runtime.

    For example::

        <room id="provider">
            <name>Test Room</name>
            <description>This is a test room.</description>
        </room>
        <room>
            <name>#provider<name>
            <description>#provider</description>
        </room>

    The above room definition would result in two rooms with the same name and
    description.

    If you changed the name on the room with the id ``provider``, the name of
    the other room would also change.

    :ivar ~earwax.story.WorldRoom.world: The world this room is part of.

        You cannot set this value in XML, as it is inferred from the tag the
        ``<room>`` tag is part of.

    :ivar ~earwax.story.WorldRoom.id: The unique ID of this room.

        If this value is not provided, then an ID will be generated, based on
        the number of rooms that have already been loaded.

        If you want to link this room with exits, it is *highly* recommended
        that you provide your own ID.

    :ivar ~earwax.story.WorldRoom.name: The name of this room, or the #id of a
        room to inherit the name from.

        This value is provided in XML with the ``<name>`` tag.

    :ivar ~earwax.story.WorldRoom.description: The description of this room, or
        the #id of another room to inherit the description from.

        This value is provided in XML with the ``<description>`` tag.

    :ivar ~earwax.story.WorldRoom.ambiances: A list of ambiances to play when
        this room is in focus.

        This value is provided in XML with a series of ``<ambiance>`` tags.

    :ivar ~earwax.story.WorldRoom.objects: A mapping of object ids to objects.

        To get a list of objects, the canonical way is to use the
        :meth:`get_objects` method, as this will properly hide objects which
        should not be shown because they are in the player's inventory.

        This value is provided in XML with a series of ``<object>`` tags.

    :ivar ~earwax.story.WorldRoom.exits: A list of exits from this room.

        This value is provided in XML as a series of ``<exit>`` tags.
    """

    world: 'StoryWorld'
    id: str
    name: str = 'Unnamed Room'
    description: str = 'Not described.'
    ambiances: List[WorldAmbiance] = attrib(
        default=Factory(list), init=False, repr=False
    )
    objects: Dict[str, RoomObject] = attrib(
        default=Factory(dict), init=False, repr=False
    )
    exits: List[RoomExit] = attrib(
        default=Factory(list), init=False, repr=False
    )

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

    def get_objects(self) -> List[RoomObject]:
        """Return a list of objects that the player can see.

        This will eventually exclude objects which are in the as yet
        unimplemented player inventory.
        """
        return list(self.objects.values())

    def to_xml(self) -> Element:
        """Dump this room."""
        e: Element = get_element('room', attrib={'id': self.id})
        e.append(get_element('name', text=self.name))
        e.append(get_element('description', text=self.description))
        ambiance: WorldAmbiance
        for ambiance in self.ambiances:
            e.append(ambiance.to_xml())
        obj: RoomObject
        # Don't use ``get_objects``, because we want to include all objects.
        for obj in self.objects.values():
            e.append(obj.to_xml())
        x: RoomExit
        for x in self.exits:
            e.append(x.to_xml())
        return e

    def __str__(self) -> str:
        """Return a string."""
        return stringify(self)


@attrs(auto_attribs=True)
class WorldMessages:
    """All the messages that can be shown to the player.

    Unlike the other classes, this class does not have its own ``to_xml``
    method. Instead, for brevity, when dumped, a :class:`StoryWorld` instance
    will include its :attr:`~StoryWorld.messages` as a series of ``<message>``
    tags.

    As a result, to create an instance, simply include ``message`` tags with
    the appropriate IDs in your ``<world>`` tag::

        <world>
            ...
            <message id="no_objects">You see nothing special.</message>
            <message id="no_actions">This is a boring object.</message>
            ...
        </world>

    Providing an ID which is *not* an attribute of this object will raise
    ``RuntimeError``, with a list of valid IDs.

    :ivar ~earwax.story.WorldMessages.no_objects: The message which is shown
        when the player cycles to an empty list of objects.

    :ivar ~earwax.story.WorldMessages.no_actions: The message which is shown
        when there are no actions for an object.

    :ivar ~earwax.story.WorldMessages.no_exits: The message which is shown when
            the player cycles to an empty list of exits.

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

        You can include the name of the object in question, by including a set
        of braces::

            <message id="actions_menu">You examine {}.</message>

    :ivar ~earwax.story.WorldMessages.main_menu: The title of the main menu.

    :ivar ~earwax.story.WorldMessages.play_game: The title of the "play game"
        entry in the main menu.

    :ivar ~earwax.story.WorldMessages.show_credits: The title of the "show
        credits" entry in the main menu.

    :ivar ~earwax.story.WorldMessages.credits_menu: The title of the credits
        menu.

    :ivar ~earwax.story.WorldMessages.welcome: The message which is shown when
        play starts.

    :ivar ~earwax.story.WorldMessages.exit: The title of the "exit" entry of
        the main menu.
    """

    # Empty category and failure messages:
    no_objects: str = 'This room is empty.'
    no_actions: str = 'There is nothing you can do with this object.'
    no_exits: str = 'There is no way out of this room.'
    room_activate: str = 'You cannot do that.'

    # Category names:
    room_category: str = 'Location'
    objects_category: str = 'Objects'
    exits_category: str = 'Exits'

    # Menu messages:
    actions_menu: str = 'You step up to {}.'
    main_menu: str = 'Main Menu'
    play_game: str = 'Play'
    show_credits: str = 'Show Credits'
    credits_menu: str = 'Credits'
    welcome: str = 'Welcome to this game.'
    exit: str = 'Exit'

    def __str__(self) -> str:
        """Return a string."""
        return 'World messages'


@attrs(auto_attribs=True)
class StoryWorld:
    """The top level world object.

    Worlds can contain rooms and messages, as well as various pieces of
    information about themselves.

    They can be created with the ``<world>`` tag::

        <world>
            <name>World Name</name>
            <author>Chris Norman &lt;chris.norman2@googlemail.com&gt;</author>
        </world>

    Worlds can be returned as an XML string with the :meth:`to_string` def

    :ivar ~earwax.story.StoryWorld.name: The name of this world.

        This value is provided in XML with the ``<name>`` tag.

    :ivar ~earwax.story.StoryWorld.author: The author of this world.

        The format of this value is arbitrary, although
        ``Author Name <author@domain.com>`` is recommended.

        Don't forget to escape any special characters, such as ``<`` and ``>``.

        This value is provided in XML with the ``<author>`` tag::

            <author>Chris Norman &lt;chris.norman2@googlemail.com&gt;</author>

    :ivar ~earwax.story.StoryWorld.main_menu_musics: A list of filenames to
        play as music while the main menu is being shown.

        This value is provided in XML as a series of ``<menumusic>`` tags::

            <menumusic>music_1.wav</menumusic>
            <menumusic>music_2.wav</menumusic>

    :ivar ~earwax.story.StoryWorld.rooms: A mapping of room IDs to rooms.

        This value is provided in XML as a series of ``<room>`` tags.

    :ivar ~earwax.story.StoryWorld.initial_room_id: The ID of the room to be
        used when first starting the game.

        This value is provided in XML with the ``<entrance>`` tag::

            <entrance>room_id</entrance>

    :ivar ~earwax.story.StoryWorld.messages: The messages object used by this
        world.

        This value is provided in XML with a series of <:class:`message
        <WorldMessages>`> tags.
    """

    name: str = 'Untitled World'
    author: str = 'Unknown'

    main_menu_musics: List[str] = Factory(list)
    rooms: Dict[str, WorldRoom] = Factory(dict)
    initial_room_id: Optional[str] = None
    messages: WorldMessages = Factory(WorldMessages)

    @property
    def initial_room(self) -> Optional[WorldRoom]:
        """Return the initial room for this world."""
        if self.initial_room_id is not None:
            return self.rooms[self.initial_room_id]
        return None

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

    def add_room(self, room: WorldRoom) -> None:
        """Add a room to this world.

        :param room: The room to add.
        """
        self.rooms[room.id] = room

    def to_document(self) -> Document:
        """Return this object as an XML document."""
        s: bytes = tostring(self.to_xml())
        return parseString(s)

    def to_string(self) -> str:
        """Return this object as pretty-printed XML."""
        d: Document = self.to_document()
        return d.toprettyxml()

    def __str__(self) -> str:
        """Return a string."""
        return f'World({self.name!r})'


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
class WorldState:
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

    @property
    def room(self) -> WorldRoom:
        """Get the current room."""
        return self.world.rooms[self.room_id]

    @property
    def category(self) -> WorldStateCategories:
        """Return the current category."""
        return list(WorldStateCategories)[self.category_index]

    @property
    def object(self) -> Optional[ObjectTypes]:
        """Return the currently focused object."""
        room: WorldRoom = self.room
        category: WorldStateCategories = self.category
        if category is WorldStateCategories.room:
            return room
        elif category is WorldStateCategories.objects:
            if self.object_index is not None:
                obj: RoomObject = room.get_objects()[self.object_index]
                return obj
        else:
            assert category is WorldStateCategories.exits
            if self.object_index is not None:
                x: RoomExit = room.exits[self.object_index]
                return x
        return None

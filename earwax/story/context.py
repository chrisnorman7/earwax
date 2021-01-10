"""Provides the StoryContext class."""

import webbrowser
from typing import List, Type

from attr import Factory, attrib, attrs

from ..game import Game
from ..menu import Menu
from ..track import Track, TrackTypes
from .edit_level import EditLevel
from .play_level import PlayLevel
from .world import RoomExit, StoryWorld, WorldRoom, WorldState


@attrs(auto_attribs=True)
class StoryContext:
    """Holds references to various objects required to make a story work."""

    game: Game
    world: StoryWorld
    edit: bool = Factory(bool)
    state: WorldState = attrib()

    @state.default
    def get_default_state(instance: 'StoryContext') -> WorldState:
        """Get a default state."""
        return WorldState(instance.world)

    main_level: PlayLevel = attrib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        """Make sure everything is in working order."""
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
        room: WorldRoom
        inaccessible_rooms: List[WorldRoom] = list(self.world.rooms.values())
        for room in self.world.rooms.values():
            x: RoomExit
            for x in room.exits:
                did: str = x.destination_id
                if did not in self.world.rooms:
                    raise RuntimeError(
                        'Invalid destination %r for exit %s of room %s.' % (
                            did, x.action.name, room.name
                        )
                    )
                if x.destination in inaccessible_rooms:
                    inaccessible_rooms.remove(x.destination)
        for room in inaccessible_rooms:
            print('WARNING: There is no way to access %s!' % room.name)
        self.state.room_id = self.world.initial_room_id
        cls: Type[PlayLevel]
        if self.edit:
            cls = EditLevel
        else:
            cls = PlayLevel
        self.main_level = cls(self.game, self)

    def earwax_bug(self) -> None:
        """Open the Earwax new issue URL."""
        webbrowser.open('https://github.com/chrisnorman7/earwax/issues/new')

    def get_main_menu(self) -> Menu:
        """Create a main menu for this world."""
        m: Menu = Menu(
            self.game, self.world.messages.main_menu, dismissible=False
        )
        path: str
        for path in self.world.main_menu_musics:
            t: Track = Track('file', path, TrackTypes.music)
            m.tracks.append(t)
        m.add_item(self.play, title=self.world.messages.play_game)
        if isinstance(self.main_level, EditLevel):
            m.add_item(self.main_level.save, title='Save')
        if self.game.credits:
            m.add_item(
                self.push_credits, title=self.world.messages.show_credits
            )
        m.add_item(self.earwax_bug, title='Report Earwax Bug')
        m.add_item(self.game.stop, title=self.world.messages.exit)
        return m

    def play(self) -> None:
        """Push the world level."""
        self.game.output(self.world.messages.welcome)
        self.game.replace_level(self.main_level)

    def push_credits(self) -> None:
        """Push the credits menu."""
        self.game.push_credits_menu(title=self.world.messages.credits_menu)

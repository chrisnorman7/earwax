"""Provides the StoryContext class."""

import os.path
import webbrowser
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Type

from attr import Factory, attrib, attrs

from ..credit import Credit
from ..editor import Editor
from ..game import Game
from ..menu import ConfigMenu, Menu
from ..sound import PannerStrategies, SoundManager
from ..track import Track, TrackTypes
from ..yaml import CLoader, load
from .edit_level import EditLevel, push_rooms_menu
from .play_level import PlayLevel
from .world import RoomExit, StoryWorld, WorldRoom, WorldState


@attrs(auto_attribs=True)
class StoryContext:
    """Holds references to various objects required to make a story work."""

    game: Game
    world: StoryWorld
    edit: bool = Factory(bool)
    logger: Logger = attrib(init=False, repr=False)

    @logger.default
    def get_default_logger(instance: 'StoryContext') -> Logger:
        """Return a default logger."""
        return getLogger(instance.world.name)

    config_file: Path = attrib(init=False, repr=False)

    @config_file.default
    def get_default_config_file(instance: 'StoryContext') -> Path:
        """Get the default configuration filename."""
        return instance.game.get_settings_path() / 'game.yaml'

    state: WorldState = attrib()

    @state.default
    def get_default_state(instance: 'StoryContext') -> WorldState:
        """Get a default state."""
        return WorldState(instance.world)

    main_level: PlayLevel = attrib(init=False, repr=False)
    errors: List[str] = Factory(list)
    warnings: List[str] = Factory(list)

    def __attrs_post_init__(self) -> None:
        """Make sure everything is in working order."""
        if self.world.initial_room_id is None:
            self.logger.critical('Initial room ID is None.')
            self.errors.append(
                'You must set the initial room for your world, with a '
                '<entrance> tag inside your <world> tag.'
            )
        elif self.world.initial_room_id not in self.world.rooms:
            self.logger.critical(
                'Invalid initial room ID: %s.', self.world.initial_room_id
            )
            self.errors.append(
                'Invalid room id for <entrance> tag: %s.' %
                self.world.initial_room_id
            )
        else:
            self.state.room_id = self.world.initial_room_id
        room: WorldRoom
        inaccessible_rooms: List[WorldRoom] = list(self.world.rooms.values())
        for room in self.world.rooms.values():
            x: RoomExit
            for x in room.exits:
                did: str = x.destination_id
                if did not in self.world.rooms:
                    self.logger.critical('Invalid exit destination: %s.', did)
                    self.errors.append(
                        'Invalid destination %r for exit %s of room %s.' % (
                            did, x.action.name, room.name
                        )
                    )
                if x.destination in inaccessible_rooms:
                    inaccessible_rooms.remove(x.destination)
        for room in inaccessible_rooms:
            msg: str = 'There is no way to access the %s room.' % room
            self.logger.warning(msg)
            self.warnings.append(msg)
        music: str
        for music in self.world.main_menu_musics:
            if not os.path.exists(music):
                self.logger.critical('Invalid main menu music %s.', music)
                self.errors.append(f'Main menu music does not exist: {music}.')
        cls: Type[PlayLevel]
        if self.edit:
            cls = EditLevel
        else:
            cls = PlayLevel
        self.logger.info('Creating %r.', cls)
        self.main_level = cls(self.game, self)
        self.game.event(self.before_run)

    def before_run(self) -> None:
        """Set the default panning strategy."""
        manager: Optional[SoundManager]
        for manager in (
            self.game.interface_sound_manager,
            self.game.ambiance_sound_manager, self.game.music_sound_manager
        ):
            if manager is not None:
                manager.default_panner_strategy = PannerStrategies[
                    self.world.panner_strategy
                ]

    def get_window_caption(self) -> str:
        """Return a suitable window title."""
        caption: str = self.world.name
        if isinstance(self.main_level, EditLevel):
            caption += f' ({self.main_level.filename})'
        return caption

    def show_warnings(self) -> None:
        """Show any generated warnings."""
        m: Menu = Menu(self.game, 'Warnings')
        warning: str
        for warning in self.warnings:
            m.add_item(self.game.pop_level, title=warning)
        self.game.push_level(m)

    def earwax_bug(self) -> None:
        """Open the Earwax new issue URL."""
        webbrowser.open('https://github.com/chrisnorman7/earwax/issues/new')

    def configure_earwax(self) -> None:
        """Push a menu that can be used to configure Earwax."""
        m: ConfigMenu = ConfigMenu(  # type: ignore[misc]
            self.game,
            'Configure Earwax', dismissible=False  # type: ignore[arg-type]
        )

        @m.item(title='Return to main menu')
        def main_menu() -> None:
            self.game.replace_level(self.get_main_menu())

        self.game.replace_level(m)

    def get_main_menu(self) -> Menu:
        """Create a main menu for this world."""
        m: Menu
        if self.errors:
            m = Menu(self.game, 'Errors', dismissible=False)
            error: str
            for error in self.errors:
                m.add_item(self.game.stop, title=error)
            m.add_item(self.earwax_bug, title='Submit bug report to Earwax')
        else:
            m = Menu(
                self.game, self.world.messages.main_menu, dismissible=False
            )
            path: str
            for path in self.world.main_menu_musics:
                t: Track = Track('file', path, TrackTypes.music)
                m.tracks.append(t)
            m.add_item(self.play, title=self.world.messages.play_game)
            m.add_item(self.load, title=self.world.messages.load_game)
            if isinstance(self.main_level, EditLevel):
                if self.warnings:
                    m.add_item(
                        self.show_warnings, title='Show warnings (%d)' %
                        len(self.warnings)
                    )
                m.add_item(self.main_level.save, title='Save story')
                m.add_item(self.configure_earwax, title='Configure Earwax')
                m.add_item(self.credits_menu, title='Add or remove credits')
                m.add_item(self.set_initial_room, title='Set initial room')
                m.add_item(self.configure_music, title='Main menu music')
                m.add_item(self.world_options, title='World options')
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
        self.state = WorldState(self.world)
        self.game.replace_level(self.main_level)

    def load(self) -> None:
        """Load an existing game, and start it."""

        def yes() -> None:
            """Perform the load."""
            if self.config_file.is_file():
                self.logger.info(
                    'Loading configuration file %s.' % self.config_file
                )
                with self.config_file.open('r') as f:
                    d: Dict[str, Any] = load(f, Loader=CLoader)
                    self.logger.info('Loaded configuration data: %r.' % d)
                self.state = WorldState(self.world, **d)
                # Remove any duplicates.
                self.state.inventory_ids = list(set(self.state.inventory_ids))
                self.main_level.build_inventory()
                self.game.output('Game loaded.')
                if len(self.game.levels) > 1:
                    self.game.pop_level()
                if self.game.level is self.main_level:
                    self.main_level.set_room(self.state.room)
                else:
                    self.play()
            else:
                self.game.output(self.world.messages.no_saved_game)

        def no() -> None:
            """Don't do anything."""
            self.game.output('Cancelled.')
            self.game.pop_level()

        if self.game.level is self.main_level:
            m: Menu = Menu.yes_no(
                self.game, yes, no,
                title='Do you want to load your saved game?'
            )
            self.game.push_level(m)
        else:
            yes()

    def push_credits(self) -> None:
        """Push the credits menu."""
        self.game.push_credits_menu(title=self.world.messages.credits_menu)

    def credit_menu(self, credit: Credit) -> Callable[[], None]:
        """Push a menu that can deal with credits."""

        def edit_name() -> Generator[None, None, None]:
            """Edit the credit name."""
            e: Editor = Editor(self.game, text=credit.name)

            @e.event
            def on_submit(text: str) -> None:
                self.game.pop_level()
                if text:
                    credit.name = text
                    self.game.output('Credit renamed.')
                    self.game.pop_level()
                    self.credit_menu(credit)()
                else:
                    self.game.output('Names cannot be blank.')

            self.game.output(
                'Enter a new name for this credit: %s' % credit.name
            )
            yield
            self.game.push_level(e)

        def edit_url() -> Generator[None, None, None]:
            """Set the URL."""
            e: Editor = Editor(self.game, text=credit.url)

            @e.event
            def on_submit(text: str) -> None:
                self.game.pop_level()
                if text:
                    credit.url = text
                    self.game.output('URL set.')
                    self.game.pop_level()
                    self.credit_menu(credit)()
                else:
                    self.game.output('The URL cannot be blank.')

            self.game.output(
                'Enter a new URL for %s: %s' % (credit.name, credit.url)
            )
            yield
            self.game.push_level(e)

        def edit_sound() -> Generator[None, None, None]:
            """Set the sound."""
            sound: str = ''
            if credit.sound is not None:
                sound = str(credit.sound)
            e: Editor = Editor(self.game, text=sound)

            @e.event
            def on_submit(text: str) -> None:
                self.game.pop_level()
                if text:
                    if os.path.exists(text):
                        credit.sound = Path(text)
                        self.game.output('Sound set.')
                        self.game.pop_level()
                        self.credit_menu(credit)()
                    else:
                        self.game.output('Path does not exist: %s.' % text)
                else:
                    self.game.output('Sound cleared.')
                    credit.sound = None
                    self.game.pop_level()
                    self.credit_menu(credit)()

            self.game.output(
                'Enter a new sound for %s: %s' % (credit.name, credit.sound)
            )
            yield
            self.game.push_level(e)

        def test_url() -> None:
            webbrowser.open(credit.url)

        def delete() -> None:

            def yes() -> None:
                self.game.credits.remove(credit)
                self.game.output('Credit deleted.')
                self.game.clear_levels()
                self.game.push_level(self.get_main_menu())

            def no() -> None:
                self.game.output('Cancelled.')
                self.game.pop_level()

            m: Menu = Menu.yes_no(self.game, yes, no)
            self.game.push_level(m)

        def close_menu() -> Generator[None, None, None]:
            self.game.output('Done.')
            yield
            self.game.clear_levels()
            self.game.push_level(self.get_main_menu())

        def inner() -> None:
            m: Menu = Menu(self.game, 'Edit Credit', dismissible=False)
            m.add_item(edit_name, title=f'Rename ({credit.name})')
            m.add_item(edit_url, title=f'Change URL ({credit.url})')
            m.add_item(edit_sound, title=f'Change sound ({credit.sound})')
            m.add_item(test_url, title='Test URL')
            m.add_item(delete, title='Delete')
            m.add_item(close_menu, title='Done')
            self.game.push_level(m)

        return inner

    def credits_menu(self) -> None:
        """Add or remove credits."""

        def add_credit() -> None:
            """Add a new credit."""
            c: Credit = Credit.earwax_credit()
            self.game.credits.append(c)
            self.credit_menu(c)()

        m: Menu = Menu(self.game, 'Configure Credits')
        m.add_item(add_credit, title='Add')
        credit: Credit
        for credit in self.game.credits:
            m.add_item(
                self.credit_menu(credit), title=f'{credit.name}: {credit.url}'
            )
        self.game.push_level(m)

    def set_initial_room(self) -> None:
        """Set the initial room."""

        def inner(room: WorldRoom) -> None:
            """Actually set the room."""
            self.world.initial_room_id = room.id
            self.game.output('Initial room set.')
        push_rooms_menu(
            self.game, [
                x for x in self.world.rooms.values()
                if x is not self.world.initial_room
            ], inner
        )

    def configure_music(self) -> None:
        """Allow adding and removing main menu music."""

        def add() -> Generator[None, None, None]:
            """Add some music."""
            e: Editor = Editor(self.game)

            @e.event
            def on_submit(text: str) -> None:
                self.game.pop_level()  # Pop the editor.
                if not text:
                    self.game.output('Cancelled.')
                elif not os.path.isfile(text):
                    self.game.output(
                        'Invalid music path: %s. File does not exist.' % text
                    )
                else:
                    self.game.pop_level()  # Pop the music menu.
                    self.world.main_menu_musics.append(text)
                    self.game.output('Music added.')
                    self.game.replace_level(self.get_main_menu())

            self.game.output('Enter the path for the new music:')
            yield
            self.game.push_level(e)

        def delete(path: str) -> Callable[[], None]:
            """Push a confirmation menu."""

            def yes() -> None:
                self.game.pop_level()
                self.world.main_menu_musics.remove(path)
                self.game.output('Deleted.')
                self.game.replace_level(self.get_main_menu())

            def no() -> None:
                self.game.pop_level()
                self.game.output('Cancelled.')

            def inner() -> None:
                self.game.replace_level(Menu.yes_no(self.game, yes, no))

            return inner

        m: Menu = Menu(self.game, 'Main Menu Music')
        m.add_item(add, title='Add')
        music: str
        for music in self.world.main_menu_musics:
            m.add_item(delete(music), title=music)
        self.game.push_level(m)

    def world_options(self) -> None:
        """Configure the world."""

        def set_name() -> Generator[None, None, None]:
            e: Editor = Editor(self.game, text=self.world.name)

            @e.event
            def on_submit(text: str) -> None:
                if not text:
                    self.game.output('Cancelled.')
                else:
                    self.world.name = text
                    self.game.output('World renamed.')
                    if self.game.window is not None:
                        self.game.window.set_caption(self.get_window_caption())
                self.game.pop_level()

            self.game.output(f'Enter a new world name: {self.world.name}')
            yield
            self.game.push_level(e)

        m: Menu = Menu(self.game, 'World Options')
        m.add_item(set_name, title='Rename')
        m.add_item(
            self.set_panner_strategy,
            title='Set panning strategy (requires restart)'
        )
        self.game.push_level(m)

    def set_panner_strategy(self) -> None:
        """Allow the changing of the panner strategy."""

        def set_strategy(strategy: PannerStrategies) -> Callable[[], None]:

            def inner() -> None:
                self.world.panner_strategy = strategy.name
                self.game.output(
                    f'Panner strategy changed to {self.world.panner_strategy}.'
                )
                manager: Optional[SoundManager]
                for manager in (
                    self.game.ambiance_sound_manager,
                    self.game.interface_sound_manager,
                    self.game.music_sound_manager
                ):
                    if manager is not None:
                        manager.default_panner_strategy = strategy
                self.game.pop_level()

            return inner

        m: Menu = Menu(
            self.game, f'Panner Strategy ({self.world.panner_strategy})'
        )
        strategy: PannerStrategies
        for strategy in PannerStrategies.__members__.values():
            m.add_item(set_strategy(strategy), title=strategy.name)
        self.game.push_level(m)

"""A quick example game."""

import sys
from synthizer import SynthizerError
from pathlib import Path
from typing import Generator, Optional

from pyglet.window import Window, key, mouse

from earwax import (ActionMenu, Config, ConfigMenu, ConfigValue, Editor,
                    FileMenu, Game, Level, tts)
from earwax.action import OptionalGenerator


class ConnectionConfig(Config):
    """Pretend connection configuration."""

    __section_name__ = 'Connection Options'
    connection_speed = ConfigValue(
        'normal', type_=('slow', 'normal', 'fast'), name='Connection speed'
    )
    tls = ConfigValue(
        True, type_=Optional[bool], name='Use TLS', value_converters={
            type(None): lambda o: 'Automatic',
            bool: lambda o: 'Enabled' if o.value else 'Disabled'
        }
    )
    timeout = ConfigValue(
        30.0, name='Connection timeout', value_converters={
            float: lambda o: f'{o.value} seconds'
        }
    )


class ServerConfig(Config):
    """Configure an imaginary server."""

    hostname = ConfigValue('localhost')
    port = ConfigValue(1234)
    connection = ConnectionConfig()


class ExampleConfig(Config):
    """Accessed with the o key."""

    __section_name__ = 'Options'
    username = ConfigValue('')
    remember = ConfigValue(True, name='Remember username')
    server = ServerConfig()
    start_script = ConfigValue(None, type_=Optional[Path], name='Start script')


class ExampleGame(Game):
    """A game with some extra stuff."""

    can_beep: bool = True


def main() -> None:
    g: ExampleGame = ExampleGame()
    level: Level = Level()
    config: ExampleConfig = ExampleConfig()
    g.push_level(level)

    @level.action('Change window title', symbol=key.T)
    def set_title() -> OptionalGenerator:
        """Set the window title to the given text."""

        def inner(text: str) -> None:
            if g.window is not None:
                g.window.set_caption(text)
            tts.speak('Title set.')
            g.pop_level()

        if g.window is not None:
            tts.speak(f'Window title: {g.window.caption}')
            yield
            g.push_level(Editor(inner, g, text=g.window.caption))

    @level.action('Quit', symbol=key.ESCAPE)
    def do_quit() -> None:
        """Quit the game."""
        if g.window is not None:
            g.window.dispatch_event('on_close')

    @level.action('Beep', symbol=key.B, interval=0.75)
    def do_beep() -> None:
        """Speak something."""
        if g.can_beep:
            sys.stdout.write('\a')
            sys.stdout.flush()

    @level.action('Mouse thing', mouse_button=mouse.LEFT)
    def mouse_thing():
        tts.speak('Mouse down.')
        yield
        tts.speak('Mouse up.')

    @level.action('Toggle beeping', symbol=key.P, mouse_button=mouse.RIGHT)
    def toggle_beep() -> None:
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @level.action('Menu', symbol=key.M)
    def menu() -> OptionalGenerator:
        """Select a file."""

        def play_sound(path: Optional[Path]) -> None:
            """Call player.play in a try block."""
            if g.interface_sound_player is not None and path is not None:
                try:
                    g.interface_sound_player.play_path(path)
                except SynthizerError:
                    pass  # Not a sound file.

        yield
        menu: FileMenu = FileMenu(Path.cwd(), play_sound, 'Select A File', g)
        g.push_level(menu)

    @level.action('Options', symbol=key.O)
    def options() -> Generator[None, None, None]:
        """Show the options menu."""
        yield
        m: ConfigMenu = ConfigMenu(config, 'Options', g)
        g.push_level(m)

    @level.action('Configure Earwax', symbol=key.C)
    def configure_earwax() -> Generator[None, None, None]:
        """Configure the earwax library."""
        yield
        m: ConfigMenu = ConfigMenu(g.config, 'Earwax Configuration', g)
        g.push_level(m)

    @level.action(
        'Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT
    )
    def show_actions() -> OptionalGenerator:
        """Show all game actions."""
        yield
        g.push_level(ActionMenu('Actions', g))

    g.run(Window(caption='Example Game'))


if __name__ == '__main__':
    main()

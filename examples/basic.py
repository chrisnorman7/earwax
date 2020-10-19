"""A quick example game."""

import sys
from pathlib import Path
from typing import Generator, Optional

from pyglet.window import Window, key, mouse
from synthizer import SynthizerError

from earwax import (ActionMenu, Config, ConfigMenu, ConfigValue, Editor,
                    FileMenu, Game, Level)
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
    can_beep = ConfigValue(True, name='Allow beeping')


g: Game = Game()
level: Level = Level(g)
config: ExampleConfig = ExampleConfig()


@level.action('Change window title', symbol=key.T, joystick_button=2)
def set_title() -> OptionalGenerator:
    """Set the window title to the given text."""
    if g.window is not None:
        g.output(f'Window title: {g.window.caption}')
        yield
        e: Editor = Editor(g, text=g.window.caption)
        g.push_level(e)

        @e.event
        def on_submit(text: str) -> None:
            if g.window is not None:
                g.window.set_caption(text)
            g.output('Title set.')
            g.pop_level()


@level.action('Quit', symbol=key.ESCAPE, joystick_button=3)
def do_quit() -> None:
    """Quit the game."""
    if g.window is not None:
        g.window.dispatch_event('on_close')


@level.action('Beep', symbol=key.B, interval=0.75, joystick_button=0)
def do_beep() -> None:
    """Speak something."""
    if config.can_beep.value:
        sys.stdout.write('\a')
        sys.stdout.flush()


@level.action('Mouse thing', mouse_button=mouse.LEFT)
def mouse_thing():
    g.output('Mouse down.')
    yield
    g.output('Mouse up.')


@level.action(
    'Toggle beeping', symbol=key.P, mouse_button=mouse.RIGHT,
    joystick_button=1
)
def toggle_beep() -> Generator[None, None, None]:
    """Toggle beeping."""
    config.can_beep.value = not config.can_beep.value
    yield
    g.output(
        f'Beeping {"enabled" if config.can_beep.value else "disabled"}.'
    )


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
    menu: FileMenu = FileMenu(
        g, 'Select A File', func=play_sound, path=Path.cwd(),
    )
    g.push_level(menu)


@level.action('Options', symbol=key.O)
def options() -> Generator[None, None, None]:
    """Show the options menu."""
    yield
    m: ConfigMenu = ConfigMenu(g, 'Options', config=config)
    g.push_level(m)


@level.action('Configure Earwax', symbol=key.C)
def configure_earwax() -> Generator[None, None, None]:
    """Configure the earwax library."""
    yield
    m: ConfigMenu = ConfigMenu(g, 'Earwax Configuration')
    g.push_level(m)


@level.action('Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
def show_actions() -> OptionalGenerator:
    """Show all game actions."""
    yield
    g.push_level(ActionMenu(g, 'Actions'))


if __name__ == '__main__':
    g.run(Window(caption='Example Game'), initial_level=level)

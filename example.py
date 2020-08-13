"""A quick example game."""

import sys
from pathlib import Path
from typing import Optional

from pyglet.window import Window, key
from synthizer import BufferGenerator, Context, DirectSource, SynthizerError

from earwax import (
    ActionMenu, AdvancedInterfaceSoundPlayer, Editor, FileMenu, Game, Level,
    SimpleInterfaceSoundPlayer, get_buffer, tts)
from earwax.action import OptionalGenerator


class ExampleGame(Game):
    """A game with some extra stuff."""

    can_beep: bool = True
    menu_sound_player: SimpleInterfaceSoundPlayer
    ctx: Context
    source: DirectSource
    generator: BufferGenerator

    def before_run(self) -> None:
        """Set up some things."""
        self.ctx = Context()
        self.source = DirectSource(self.ctx)
        self.generator = BufferGenerator(self.ctx)
        self.generator.looping = True
        self.menu_sound_player = SimpleInterfaceSoundPlayer(
            self.ctx, BufferGenerator(self.ctx)
        )
        self.menu_sound_player.generator.buffer = get_buffer(
            'file', 'move.wav'
        )


def main() -> None:
    g: ExampleGame = ExampleGame()
    level: Level = Level()
    g.push_level(level)

    def file_selected(name: Optional[Path]) -> OptionalGenerator:
        """A file has been chosen."""
        g.pop_level()
        try:
            g.source.remove_generator(g.generator)
        except SynthizerError:
            pass  # No worries.
        if name is not None:
            try:
                buffer = get_buffer('file', str(name))
                g.generator.buffer = buffer
                g.source.add_generator(g.generator)
            except SynthizerError as e:
                tts.speak(str(e))
        return None

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

    @level.action('Toggle beeping', symbol=key.P)
    def toggle_beep() -> None:
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @level.action('Menu', symbol=key.M)
    def menu() -> OptionalGenerator:
        """Select a file."""
        player: AdvancedInterfaceSoundPlayer = AdvancedInterfaceSoundPlayer(
            g.ctx, play_directories=False
        )

        def play_sound(path: Path) -> None:
            """Call player.play in a try block."""
            try:
                player.play_path(path)
            except SynthizerError:
                pass  # Not a sound file.

        yield
        menu: FileMenu = FileMenu(
            Path.cwd(), file_selected, 'Select A File', g
        )
        g.push_level(menu)

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

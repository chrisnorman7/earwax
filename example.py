"""A quick example game."""

import sys
from pathlib import Path
from typing import Generator, Optional

from pyglet.window import key

from earwax import (
    ActionMenu, AdvancedInterfaceSoundPlayer, Editor, FileMenu, Game,
    SimpleInterfaceSoundPlayer, get_buffer, tts)
from synthizer import BufferGenerator, Context, DirectSource, SynthizerError


class ExampleGame(Game):
    """A game with some extra stuff."""

    def before_run(self) -> None:
        self.can_beep = True
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


def main():
    g: ExampleGame = ExampleGame('Example')

    def file_selected(name: Optional[Path]) -> Optional[Generator[
        None, None, None]
    ]:
        """A file has been chosen."""
        g.clear_menus()
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

    def _set_title(text: str) -> None:
        """Set the window title to the given text."""
        g.editor = None
        if g.window is not None:
            g.window.set_caption(text)
        tts.speak('Title set.')

    @g.action('Quit', symbol=key.ESCAPE)
    def do_quit() -> None:
        """Quit the game."""
        if g.window is not None:
            g.window.close()

    @g.action(
        'Beep', symbol=key.B, interval=0.75,
        can_run=lambda: g.can_beep and g.normal()
    )
    def do_beep() -> None:
        """Speak something."""
        sys.stdout.write('\a')
        sys.stdout.flush()

    @g.action('Toggle beeping', symbol=key.P)
    def toggle_beep() -> None:
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @g.action('Menu', symbol=key.M)
    def menu() -> Generator[None, None, None]:
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
            g, 'Select a file', Path.cwd(), file_selected,
            on_selected=play_sound
        )
        g.push_menu(menu)

    @g.action(
        'Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT
    )
    def show_actions() -> None:
        """Show all game actions."""
        g.push_menu(ActionMenu(g, on_selected=g.menu_sound_player.play))

    @g.action('Set window title', symbol=key.T)
    def set_title(text: Optional[str] = None) -> Generator[
        None, None, None
    ]:
        """Change the window title."""
        yield
        if g.window is not None:
            g.editor = Editor(_set_title, text=g.window.caption)
            tts.speak(f'Window title: {g.editor.text}')

    g.add_default_actions()
    g.run()


if __name__ == '__main__':
    main()

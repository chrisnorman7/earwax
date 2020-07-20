"""A quick example game."""

import os
import sys

from pyglet.window import key

from earwax import (ActionMenu, Editor, FileMenu, Game,
                    SimpleInterfaceSoundPlayer, get_buffer, tts,
                    AdvancedInterfaceSoundPlayer)
from synthizer import BufferGenerator, Context, DirectSource, SynthizerError


class ExampleGame(Game):
    """A game with some extra stuff."""
    def before_run(self):
        self.can_beep = True
        self.ctx = Context()
        self.source = DirectSource(g.ctx)
        self.generator = BufferGenerator(g.ctx)
        self.generator.looping = True
        self.menu_sound_player = SimpleInterfaceSoundPlayer(
            self.ctx, BufferGenerator(self.ctx)
        )
        self.menu_sound_player.generator.buffer = get_buffer(
            'file', 'move.wav'
        )


if __name__ == '__main__':
    g = ExampleGame('Example')

    def file_selected(name):
        """A file has been chosen."""
        g.clear_menus()
        try:
            g.source.remove_generator(g.generator)
        except SynthizerError:
            pass  # No worries.
        if name is not None:
            try:
                buffer = get_buffer(g.ctx, 'file', name)
                g.generator.buffer = buffer
                g.source.add_generator(g.generator)
            except SynthizerError as e:
                tts.speak(str(e))

    def on_file_item(path, item):
        """A menu item has been created as a result of a path."""
        try:
            buffer = get_buffer(g.ctx, 'file', path)
            item.generator = BufferGenerator(g.ctx)
            item.generator.buffer = buffer
        except SynthizerError:
            pass

    def _set_title(text):
        """Set the window title to the given text."""
        g.editor = None
        g.window.set_caption(text)
        tts.speak('Title set.')

    @g.action('Quit', symbol=key.ESCAPE)
    def do_quit():
        """Quit the game."""
        g.window.close()

    @g.action(
        'Beep', symbol=key.B, interval=0.75,
        can_run=lambda: g.can_beep and g.normal()
    )
    def do_beep():
        """Speak something."""
        sys.stdout.write('\a')
        sys.stdout.flush()

    @g.action('Toggle beeping', symbol=key.P)
    def toggle_beep():
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @g.action('Menu', symbol=key.M)
    def menu():
        """Select a file."""
        player = AdvancedInterfaceSoundPlayer(g.ctx, play_directories=False)

        def play_sound(path):
            """Call player.play in a try block."""
            try:
                player.play(path)
            except SynthizerError:
                pass  # Not a sound file.
        menu = FileMenu(
            g, 'Select a file', os.getcwd(), file_selected,
            on_selected=play_sound
        )
        g.push_menu(menu)

    @g.action(
        'Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT
    )
    def show_actions():
        """Show all game actions."""
        g.push_menu(ActionMenu(g, on_selected=g.menu_sound_player.play))

    @g.action('Set window title', symbol=key.T)
    def set_title(text=None):
        """Change the window title."""
        yield
        g.editor = Editor(_set_title, text=g.window.caption)
        tts.speak(f'Window title: {g.editor.text}')

    g.add_default_actions()
    g.run()

"""A quick example game."""

import os
import sys

from pyglet.window import key

from earwax import ActionMenu, FileMenu, Game, get_buffer, tts
from earwax.editor import Editor
from synthizer import BufferGenerator, Context, DirectSource, SynthizerError

if __name__ == '__main__':
    g = Game('Example')
    g.can_beep = True
    g.ctx = None
    g.source = None
    g.generator = None

    def file_selected(name):
        """A file has been chosen."""
        g.clear_menus()
        if g.ctx is None:
            g.ctx = Context()
        if g.source is None:
            g.source = DirectSource(g.ctx)
        if g.generator is None:
            g.generator = BufferGenerator(g.ctx)
            g.generator.looping = True
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

    @g.action('Quit', symbol=key.ESCAPE, can_run=g.normal)
    def do_quit():
        """Quit the game."""
        g.window.close()

    @g.action(
        'Beep', symbol=key.B, interval=0.75,
        can_run=lambda: g.can_beep and g.no_menu
    )
    def do_beep():
        """Speak something."""
        sys.stdout.write('\a')
        sys.stdout.flush()

    @g.action('Toggle beeping', symbol=key.P, can_run=g.normal)
    def toggle_beep():
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @g.action('Menu', symbol=key.M, can_run=g.normal)
    def menu():
        """Select a file."""
        menu = FileMenu(
            g, 'Select a file', os.getcwd(), file_selected
        )
        g.push_menu(menu)

    @g.action(
        'Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT,
        can_run=g.normal
    )
    def show_actions():
        """Show all game actions."""
        g.push_menu(ActionMenu(g))

    @g.action('Set window title', symbol=key.T, can_run=g.normal)
    def set_title():
        """Change the window title."""
        yield
        g.editor = Editor(text=g.window.caption)
        tts.speak(f'Window title: {g.editor.text}')

    g.add_menu_actions()
    g.run()

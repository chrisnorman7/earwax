"""A quick example program."""

import os
import sys

from pyglet.window import key

from cage import Game, tts
from cage.menu import FileMenu

if __name__ == '__main__':
    g = Game('Example')
    g.can_beep = True

    def file_selected(name):
        """A file has been chosen."""
        g.clear_menus()
        tts.speak(f'You chose {name}.')

    @g.action('Quit', symbol=key.ESCAPE, can_run=g.no_menu)
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

    @g.action('Toggle beeping', symbol=key.P, can_run=g.no_menu)
    def toggle_beep():
        """Toggle beeping."""
        g.can_beep = not g.can_beep
        tts.speak(f'Beeping {"enabled" if g.can_beep else "disabled"}.')

    @g.action('Menu', symbol=key.M, can_run=g.no_menu)
    def menu():
        """Select a file."""
        menu = FileMenu(
            g, 'Select a file', os.getcwd(), file_selected
        )
        g.push_menu(menu)

    g.add_menu_actions()
    g.run()

"""A quick example game."""

import os
import sys

from pyglet.window import key

from earwax import ActionMenu, FileMenu, Game, tts

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

    @g.action(
        'Show actions', symbol=key.SLASH, modifiers=key.MOD_SHIFT,
        can_run=g.no_menu
    )
    def show_actions():
        """Show all game actions."""
        g.push_menu(ActionMenu(g))

    g.add_menu_actions()
    g.run()

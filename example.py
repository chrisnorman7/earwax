"""A quick example program."""

import sys

from pyglet.window import key

from cage import Game, tts

if __name__ == '__main__':
    g = Game('Example')

    g.can_beep = True

    @g.action('Quit', symbol=key.ESCAPE)
    def do_quit():
        """Quit the game."""
        g.window.close()

    @g.action(
        'Beep', symbol=key.B, interval=0.75,
        can_run=lambda game: game.can_beep
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
    g.run()

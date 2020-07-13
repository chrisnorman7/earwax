"""A quick example program."""

import sys

from pyglet.window import key

from cage import Game

if __name__ == '__main__':
    g = Game('Example')

    @g.action('Quit', symbol=key.ESCAPE)
    def do_quit():
        """Quit the game."""
        g.window.close()

    @g.action('Beep', symbol=key.B, interval=0.75)
    def do_beep():
        """Speak something."""
        sys.stdout.write('\a')
        sys.stdout.flush()
    g.run()

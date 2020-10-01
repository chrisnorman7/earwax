"""Provides the new subcommand."""

import sys
from argparse import Namespace
from datetime import datetime

src = '''"""A game created by `{}` on {}."""

from earwax import Game, Level, tts

from pyglet.window import Window, key

game: Game = Game(name='New Earwax Game')
window: Window = Window(caption=game.name)

level: Level = Level(game)


@level.action('Test', symbol=key.T, joystick_button=0)
def test_game() -> None:
    """Prove your new game works."""
    tts.speak('Earwax game working.')


@level.action('Quit', symbol=key.ESCAPE)
def do_quit() -> None:
    """Close the game window."""
    window.dispatch_event('on_close')


if __name__ == '__main__':
    game.run(window, initial_level=level)
'''


def new(args: Namespace) -> None:
    """Create a new game."""
    source: str = src.format(' '.join(sys.argv), datetime.now())
    args.filename.write(source)
    args.filename.close()
    print('Wrote new game file at %s.' % args.filename.name)

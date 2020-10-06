"""This script shows you how you can lever the power of the Pyglet event system
in your own games.

As you can see from the below code, it's not exactly the most intuative code
ever, and not great to maintain. That is after all why Earwax does the things
it does.

This code works because both ``earwax.Game``, and ``earwax.level`` (as well as
all subclasses) inherit from ``pyglet.event.EventDispatcher``.

The downsite of course is that you can't see the custom keys in the actions
menu, which makes them effectively hidden from the player, unless you provided
some other help system for just those keys.
"""

from pyglet.event import EVENT_HANDLED, EVENT_UNHANDLED
from pyglet.window import Window, key

from earwax import ActionMenu, Game, Level, tts

keys = (
    key._1, key._2, key._3, key._4, key._5, key._6, key._7, key._8, key._9,
    key._0
)

game = Game()
window = Window(caption='Testing')

level = Level(game)


@game.event
def on_key_press(symbol, modifiers):
    if symbol in keys and not modifiers:
        tts.speak(f'Position {keys.index(symbol)}.')
        return EVENT_HANDLED
    elif symbol == key.ESCAPE and not modifiers and game.level is level:
        window.dispatch_event('on_close')
    else:
        return EVENT_UNHANDLED


@level.action('Cause problems', symbol=key._0)
def problem():
    raise RuntimeError('This should never happen.')


@level.action('Show help', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
def get_help():
    game.push_level(ActionMenu(game, 'Actions'))


if __name__ == '__main__':
    game.run(window, initial_level=level)

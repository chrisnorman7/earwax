"""The below script uses a for loop to create actions bound to a series of
keys, to simulate the keys you might use for reviewing game messages for
example.

You could do this with a class with a custom ``__call__`` method if you wanted
to, but this way is less typing.

I've included the help command (shift + /) to demonstrate what they entries in
that menu would look like.
"""

from pyglet.window import Window, key

from earwax import ActionMenu, Game, Level, tts

game = Game()

level = Level(game)

for i, x in enumerate(
    (
        key._1, key._2, key._3, key._4, key._5, key._6, key._7, key._8, key._9,
        key._0
    )
):
    @level.action(f'Read message {i + 1}', symbol=x)
    def speak(pos=i):
        tts.speak(f'Position {pos}.')


@level.action('Show help', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
def get_help():
    game.push_level(ActionMenu(game, 'Actions'))


if __name__ == '__main__':
    window = Window(caption='Testing')
    game.run(window, initial_level=level)

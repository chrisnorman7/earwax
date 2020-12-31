"""An example of rumble."""

if True:
    import sys
    sys.path.insert(0, '..')

from pyglet.input import Joystick
from pyglet.window import Window, key

from earwax import Game, Level, SdlError

game: Game = Game(name='Rumble Example')

level: Level = Level(game)


@level.register_and_bind
def on_joyaxis_motion(joystick: Joystick, axis: str, value: float):
    """Handle joystick motion."""
    if axis not in ('y', 'ry'):
        return None
    index: int = game.joysticks.index(joystick)
    if value <= 0:
        try:
            game.stop_rumble(index)
        except SdlError:
            pass  # Not started rumbling yet.
    else:
        game.start_rumble(index, value, 0)


@level.register_and_bind
def on_joybutton_press(joystick: Joystick, button: int) -> None:
    """Start rumbles.

    If ``button`` is ``0``, quit the game.
    """
    num_buttons: int = len(joystick.buttons)
    v: float = ((100 / num_buttons) * button) / 100
    if button == 0:
        return game.stop()
    game.start_rumble(game.joysticks.index(joystick), v, 0)


@level.register_and_bind
def on_joybutton_release(joystick: Joystick, button: int) -> None:
    """Stop vibrations."""
    game.stop_rumble(game.joysticks.index(joystick))


@level.action('Show help', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
def show_help() -> None:
    """Tell 'em what to do."""
    game.output('Move the joysticks and press buttons for rumbles.')


if __name__ == '__main__':
    window: Window = Window(caption=game.name)
    game.run(window, initial_level=level)

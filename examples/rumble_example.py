"""An example of rumble."""

if True:
    import sys
    sys.path.insert(0, '..')

from pyglet.input import Joystick
from pyglet.window import Window, key

from earwax import Game, Level, RumbleEffect, SdlError

game: Game = Game(name='Rumble Example')
effect: RumbleEffect = RumbleEffect(
    0.2,  # start_value
    0.3,  # increase_interval
    0.1,  # increase_value
    1.5,  # peak_duration
    1.0,  # peak_value
    0.3,  # decrease_interval
    0.1,  # decrease_value
    0.1,  # end_value
)

level: Level = Level(game)


@level.register_and_bind
def on_joyaxis_motion(joystick: Joystick, axis: str, value: float):
    """Handle joystick motion."""
    if axis not in ('y', 'ry'):
        return None
    if value <= 0:
        try:
            game.stop_rumble(joystick)
        except SdlError:
            pass  # Not started rumbling yet.
    else:
        game.start_rumble(joystick, value, 0)


@level.register_and_bind
def on_joybutton_press(joystick: Joystick, button: int) -> None:
    """Start rumbles.

    If ``button`` is ``0``, quit the game.

    If ``button`` is ``1``, make a pretty pattern.
    """
    num_buttons: int = len(joystick.buttons)
    v: float = ((100 / num_buttons) * button) / 100
    if button == 0:
        return game.stop()
    elif button == 1:
        return effect.start(game, joystick).run()
    game.start_rumble(joystick, v, 0)


@level.register_and_bind
def on_joybutton_release(joystick: Joystick, button: int) -> None:
    """Stop vibrations."""
    game.stop_rumble(joystick)


@level.action('Show help', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
def show_help() -> None:
    """Tell 'em what to do."""
    game.output('Move the joysticks and press buttons for rumbles.')


if __name__ == '__main__':
    window: Window = Window(caption=game.name)
    game.run(window, initial_level=level)
